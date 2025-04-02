"""
Handles model inference operations
"""
import logging
import torch

logger = logging.getLogger(__name__)

class InferenceEngine:
    """Handles generation and inference with language models"""
    
    def __init__(self, model, tokenizer, device_config):
        self.model = model
        self.tokenizer = tokenizer
        self.device_config = device_config
        self.main_device = torch.device(device_config['main_device'])
        
    def generate_response(self, prompt, pipeline_stages=None):
        """Generate a response from the model"""
        try:
            if self.model is None or self.tokenizer is None:
                raise ValueError("Model or tokenizer not loaded")
            
            # Tokenize and prepare input
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=1024)
            
            # Move inputs to main device
            inputs = {key: val.to(self.main_device) for key, val in inputs.items()}
            
            logger.debug("Generating response...")
            # Generate response with the causal language model
            with torch.no_grad():
                # If we're using pipeline parallelism, handle it differently
                if pipeline_stages is not None:
                    # Custom forward pass through pipeline stages
                    output = self._pipeline_generate(inputs["input_ids"], pipeline_stages)
                else:
                    # Standard generation
                    output = self.model.generate(
                        inputs["input_ids"],
                        max_length=1024,
                        do_sample=True,
                        top_p=0.9,
                        temperature=0.6,
                        num_return_sequences=1
                    )
            
            logger.debug("Decoding generated response...")
            # Decode the generated response
            generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
            
            # Extract just the response part (after "Assistant:")
            response_text = generated_text.split("Assistant:", 1)[-1].strip()
            logger.info(f"Generated response: {response_text[:50]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
            
    def _pipeline_generate(self, input_ids, pipeline_stages):
        """Custom generation logic for pipeline parallelism"""
        try:
            # We'll implement a simple auto-regressive generation
            current_ids = input_ids.clone()
            max_length = 1024
            
            while current_ids.size(1) < max_length:
                # Process through pipeline stages
                embeddings = pipeline_stages['embeddings'](current_ids)
                if 'pos_embeddings' in pipeline_stages:
                    position_ids = torch.arange(0, current_ids.size(1), dtype=torch.long,
                                            device=current_ids.device)
                    position_embeddings = pipeline_stages['pos_embeddings'](position_ids)
                    hidden_states = embeddings + position_embeddings
                else:
                    hidden_states = embeddings
                
                # Process through early layers on primary device
                hidden_states = pipeline_stages['early_layers'](hidden_states)
                
                # Transfer to secondary device for late layers
                hidden_states = hidden_states.to(pipeline_stages['late_layers'].device)
                hidden_states = pipeline_stages['late_layers'](hidden_states)
                
                # Final output processing
                hidden_states = pipeline_stages['output_head'](hidden_states)
                
                # Get the next token prediction
                next_token_logits = self.model.lm_head(hidden_states[:, -1, :])
                next_token = next_token_logits.argmax(dim=-1).unsqueeze(-1)
                
                # Append to the sequence
                current_ids = torch.cat([current_ids, next_token], dim=-1)
                
                # Stop if end of sequence token is generated
                if next_token.item() == self.tokenizer.eos_token_id:
                    break
                    
            return current_ids
            
        except Exception as e:
            logger.error(f"Pipeline generation failed: {str(e)}")
            # Fall back to standard generation on the main device
            logger.warning("Falling back to standard generation")
            self.model.to(self.main_device)
            return self.model.generate(
                input_ids,
                max_length=1024,
                do_sample=True,
                top_p=0.9,
                temperature=0.6,
                num_return_sequences=1
            )
