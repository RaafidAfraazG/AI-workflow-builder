class PromptBuilder:
    def build_prompt(self, user_query: str, context: str = "", custom_prompt: str = "") -> str:
        """Build a prompt from user query, context, and custom template.
        
        Supports {user_query} and {context} placeholders in custom_prompt.
        If context is available but {context} is missing from the custom prompt,
        the context is automatically prepended so it is never silently dropped.
        """
        if custom_prompt:
            prompt = custom_prompt
            prompt = prompt.replace("{user_query}", user_query)
            prompt = prompt.replace("{context}", context)

            # If context exists but the placeholder wasn't in the template,
            # prepend it so the LLM always sees the retrieved knowledge.
            if context and "{context}" not in custom_prompt:
                prompt = f"Context:\n{context}\n\n{prompt}\n\nUser Question: {user_query}\n\nAnswer:"
            elif "{user_query}" not in custom_prompt:
                # No user_query placeholder either — append it
                prompt = f"{prompt}\n\nUser Question: {user_query}\n\nAnswer:"
            return prompt

        # Default prompt template
        base_prompt = "You are a helpful AI assistant. Answer the user's question based on the provided context."

        if context:
            return f"""{base_prompt}

Context:
{context}

User Question: {user_query}

Answer:"""
        else:
            return f"""{base_prompt}

User Question: {user_query}

Answer:"""