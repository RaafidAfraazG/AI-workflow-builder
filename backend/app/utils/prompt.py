class PromptBuilder:
    def build_prompt(self, user_query: str, context: str = "", custom_prompt: str = "") -> str:
        """Build a prompt from user query, context, and custom template"""
        
        if custom_prompt:
            # Use custom prompt template
            prompt = custom_prompt
            prompt = prompt.replace("{user_query}", user_query)
            prompt = prompt.replace("{context}", context)
            return prompt
        
        # Default prompt template
        base_prompt = "You are a helpful AI assistant. Answer the user's question based on the provided context."
        
        if context:
            prompt = f"""{base_prompt}

Context:
{context}

User Question: {user_query}

Answer:"""
        else:
            prompt = f"""{base_prompt}

User Question: {user_query}

Answer:"""
        
        return prompt