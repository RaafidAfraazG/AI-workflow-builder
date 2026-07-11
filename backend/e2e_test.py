import requests, json, sys
from uuid import uuid4

BASE = 'http://localhost:8000'
ERRORS = []

def step(label, ok, detail=''):
    status = 'PASS' if ok else 'FAIL'
    print(f'[{status}] {label}', f'  -> {detail}' if detail else '')
    if not ok:
        ERRORS.append(label)

print('='*60)
print('END-TO-END API TEST')
print('='*60)

# 1. Health check
r = requests.get(f'{BASE}/')
step('Health check', r.status_code == 200, r.json().get('message',''))

# 2. List workflows
r = requests.get(f'{BASE}/api/workflows/')
step('GET /api/workflows/', r.status_code == 200, f'{len(r.json())} workflows')

# 3. Create workflow with all 4 nodes + 3 edges (unique IDs each run)
nq   = str(uuid4())
nkb  = str(uuid4())
nllm = str(uuid4())
nout = str(uuid4())

workflow_payload = {
    'name': 'E2E Test Workflow',
    'nodes': [
        {'id': nq,   'type': 'userQuery',     'position': {'x': 0,   'y': 0},
         'data': {'label': 'User Query',    'config': {'placeholder': 'Ask me anything'}}},
        {'id': nkb,  'type': 'knowledgeBase', 'position': {'x': 300, 'y': 0},
         'data': {'label': 'Knowledge Base', 'config': {'collection': '', 'top_k': 5}}},
        {'id': nllm, 'type': 'llmEngine',     'position': {'x': 600, 'y': 0},
         'data': {'label': 'LLM Engine', 'config': {'customPrompt': 'Answer based on provided context.'}}},
        {'id': nout, 'type': 'output',         'position': {'x': 900, 'y': 0},
         'data': {'label': 'Output', 'config': {'format': 'text'}}},
    ],
    'edges': [
        {'id': str(uuid4()), 'source': nq,   'target': nkb,  'type': 'default'},
        {'id': str(uuid4()), 'source': nkb,  'target': nllm, 'type': 'default'},
        {'id': str(uuid4()), 'source': nllm, 'target': nout, 'type': 'default'},
    ]
}
r = requests.post(f'{BASE}/api/workflows/', json=workflow_payload)
wf_ok = r.status_code == 200
detail = f'id={r.json()["id"]}' if wf_ok else r.text[:300]
step('POST /api/workflows/ (create, 4 nodes, 3 edges)', wf_ok, detail)
if not wf_ok:
    print('FATAL: Cannot continue'); sys.exit(1)

wf = r.json()
wf_id = wf['id']
print(f'  Workflow ID: {wf_id}')
print(f'  Nodes: {len(wf["nodes"])}, Edges: {len(wf["edges"])}')

# 4. List shows workflow
r2 = requests.get(f'{BASE}/api/workflows/')
found = any(w['id'] == wf_id for w in r2.json())
step('GET /api/workflows/ (includes new workflow)', r2.status_code == 200 and found, f'{len(r2.json())} total')

# 5. Get single workflow
r3 = requests.get(f'{BASE}/api/workflows/{wf_id}')
step('GET /api/workflows/{id}', r3.status_code == 200, f'name={r3.json().get("name")}')

# 6. Upload test PDF (collection = workflow_id so it gets linked)
with open('test_kb_doc.pdf', 'rb') as f:
    r4 = requests.post(
        f'{BASE}/api/kb/upload',
        files={'file': ('test_kb_doc.pdf', f, 'application/pdf')},
        data={'collection': wf_id}
    )
upload_ok = r4.status_code == 200
detail = f'doc_id={r4.json().get("id")}' if upload_ok else r4.text[:300]
step('POST /api/kb/upload', upload_ok, detail)
doc_id = r4.json()['id'] if upload_ok else None
if doc_id:
    print(f'  Document ID: {doc_id}')
    print(f'  Workflow linked: {r4.json().get("workflow_id")}')

# 7. Ingest document (embed into ChromaDB)
if doc_id:
    r5 = requests.post(f'{BASE}/api/kb/ingest/{doc_id}')
    ingest_ok = r5.status_code == 200
    detail = r5.json().get('message','') if ingest_ok else r5.text[:300]
    step('POST /api/kb/ingest/{id}', ingest_ok, detail)

# 8. Build (validate) workflow
r6 = requests.post(f'{BASE}/api/workflows/{wf_id}/build')
build_ok = r6.status_code == 200
detail = r6.json().get('message','') if build_ok else r6.text[:300]
step('POST /api/workflows/{id}/build', build_ok, detail)

# 9. Create chat session
r7 = requests.post(f'{BASE}/api/workflows/{wf_id}/chat')
chat_ok = r7.status_code == 200
detail = f'chat_id={r7.json().get("id")}' if chat_ok else r7.text[:300]
step('POST /api/workflows/{id}/chat', chat_ok, detail)
if not chat_ok:
    print('FATAL: Cannot test chat'); sys.exit(1)
chat_id = r7.json()['id']

# 10. Send message and collect streaming response
print()
print('Sending: "What is the pricing of the Pro Plan?"')
r8 = requests.post(
    f'{BASE}/api/workflows/{wf_id}/chat/{chat_id}/message',
    json={'content': 'What is the pricing of the Pro Plan?'},
    stream=True,
    timeout=90
)
step('POST .../message (status)', r8.status_code == 200, f'HTTP {r8.status_code}')

if r8.status_code == 200:
    full_response = ''
    for line in r8.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                data = line_str[6:]
                if data == '[DONE]':
                    break
                try:
                    parsed = json.loads(data)
                    if 'token' in parsed:
                        full_response += parsed['token']
                except:
                    pass
    step('Stream response non-empty', len(full_response) > 10, f'{len(full_response)} chars')
    print(f'  Response: {full_response[:500]}')
    has_pricing = '99' in full_response or 'Pro' in full_response or 'pricing' in full_response.lower()
    step('Response contains pricing info from KB', has_pricing)
else:
    print(f'  Error: {r8.text[:300]}')

print()
print('='*60)
if ERRORS:
    print(f'FAILED STEPS: {ERRORS}')
    sys.exit(1)
else:
    print('ALL TESTS PASSED!')
print('='*60)
