"""
AI-powered Sleep Animal Generator
Generates unique weekly sleep spirit animals with descriptions and images.
"""
import configparser
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import requests
import base64
import os
from typing import Dict, Optional, Any
import random


class SleepAnimalGenerator:
    """Generate weekly sleep animals using AI based on sleep patterns."""
    
    def __init__(self, config_file='ai_config.ini'):
        """Initialize with AI config file."""
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        if Path(config_file).exists():
            self.config.read(config_file)
        else:
            print(f"⚠️ AI config file {config_file} not found. Copy from template and add API keys.")
            self.config = None
        
        # Debug settings
        self.debug_enabled = self.config.getboolean('debug', 'enable_api_logging', fallback=True) if self.config else True
        self.verbose = self.config.getboolean('debug', 'verbose_output', fallback=True) if self.config else True
        self.save_prompts = self.config.getboolean('debug', 'save_prompts', fallback=True) if self.config else True
        
        # Cache directory for generated animals
        self.cache_dir = Path('sleep_animals_cache')
        self.cache_dir.mkdir(exist_ok=True)
        
        # Debug directory for prompts and responses
        if self.save_prompts:
            self.debug_dir = Path('debug_ai_logs')
            self.debug_dir.mkdir(exist_ok=True)
    
    def debug_log(self, message: str, level: str = "INFO"):
        """Log debug messages if debugging enabled."""
        if self.debug_enabled:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"🔧 [{timestamp}] [{level}] {message}")
    
    def save_debug_file(self, filename: str, content: str):
        """Save debug content to file."""
        if self.save_prompts and hasattr(self, 'debug_dir'):
            try:
                debug_file = self.debug_dir / filename
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.debug_log(f"Saved debug file: {debug_file}")
            except Exception as e:
                self.debug_log(f"Failed to save debug file {filename}: {e}", "ERROR")
    
    def save_image_to_file(self, image_data_url: str, provider: str) -> Optional[str]:
        """Save base64 image data to file."""
        try:
            # Create images directory if it doesn't exist
            images_dir = Path('sleep_animal_images')
            images_dir.mkdir(exist_ok=True)
            
            # Extract base64 data from data URL
            if image_data_url.startswith('data:image'):
                # Format: data:image/png;base64,<base64_data>
                header, base64_data = image_data_url.split(',', 1)
                # Get image format from header
                if 'png' in header:
                    ext = 'png'
                elif 'jpeg' in header or 'jpg' in header:
                    ext = 'jpg'
                else:
                    ext = 'png'  # Default
            else:
                # Assume it's just base64 data
                base64_data = image_data_url
                ext = 'png'
            
            # Generate filename with timestamp and provider
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sleep_animal_{provider}_{timestamp}.{ext}"
            file_path = images_dir / filename
            
            # Decode and save
            import base64
            image_bytes = base64.b64decode(base64_data)
            
            with open(file_path, 'wb') as f:
                f.write(image_bytes)
            
            self.debug_log(f"💾 Saved {len(image_bytes)} bytes to {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.debug_log(f"❌ Failed to save image: {e}", "ERROR")
            return None
        
    def is_configured(self) -> bool:
        """Check if AI services are properly configured."""
        if not self.config:
            self.debug_log("No config loaded", "ERROR")
            return False
            
        # Check if we have at least one text generation API configured
        openai_key = self.config.get('openai', 'api_key', fallback='').strip()
        anthropic_key = self.config.get('anthropic', 'api_key', fallback='').strip()
        openrouter_key = self.config.get('openrouter', 'api_key', fallback='').strip()
        
        self.debug_log(f"OpenAI key: '{openai_key}' (length: {len(openai_key)})", "DEBUG")
        self.debug_log(f"Anthropic key: '{anthropic_key}' (length: {len(anthropic_key)})", "DEBUG")
        self.debug_log(f"OpenRouter key: '{openrouter_key}' (length: {len(openrouter_key)})", "DEBUG")
        
        has_openai = openai_key and openai_key != 'YOUR_OPENAI_API_KEY'
        has_anthropic = anthropic_key and anthropic_key != 'YOUR_ANTHROPIC_API_KEY'
        has_openrouter = openrouter_key and openrouter_key != 'YOUR_OPENROUTER_API_KEY'
        
        self.debug_log(f"Has OpenAI: {has_openai}", "DEBUG")
        self.debug_log(f"Has Anthropic: {has_anthropic}", "DEBUG")
        self.debug_log(f"Has OpenRouter: {has_openrouter}", "DEBUG")
        
        has_text_api = has_openai or has_anthropic or has_openrouter
        self.debug_log(f"Overall configured: {has_text_api}", "INFO")
        
        return has_text_api
    
    def get_week_identifier(self) -> str:
        """Get current week identifier for caching."""
        # Use Monday as start of week
        today = datetime.now()
        days_since_monday = today.weekday()
        monday = today - timedelta(days=days_since_monday)
        return monday.strftime('%Y-W%U')
    
    def get_cached_animal(self) -> Optional[Dict]:
        """Get cached animal for current week."""
        week_id = self.get_week_identifier()
        cache_file = self.cache_dir / f'{week_id}.json'
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def cache_animal(self, animal_data: Dict):
        """Cache generated animal data."""
        week_id = self.get_week_identifier()
        cache_file = self.cache_dir / f'{week_id}.json'
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(animal_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to cache animal data: {e}")
    
    def analyze_sleep_patterns(self, sleep_data) -> Dict:
        """Analyze recent sleep data for AI context."""
        if sleep_data is None or len(sleep_data) == 0:
            return {
                'avg_duration': 7.5,
                'consistency': 'unknown',
                'quality': 'moderate',
                'pattern': 'regular'
            }
        
        # Calculate basic metrics from DataFrame
        if 'minutesAsleep' in sleep_data.columns:
            durations = sleep_data['minutesAsleep'] / 60  # Convert minutes to hours
        elif 'hoursAsleep' in sleep_data.columns:
            durations = sleep_data['hoursAsleep']
        else:
            durations = [7.5]  # Default fallback
            
        avg_duration = durations.mean() if len(durations) > 0 else 7.5
        
        # Determine patterns
        consistency = 'consistent' if durations.std() <= 1.0 else 'variable'
        quality = 'good' if avg_duration >= 7 else 'needs_improvement'
        
        return {
            'avg_duration': round(avg_duration, 1),
            'consistency': consistency,
            'quality': quality,
            'nights_tracked': len(sleep_data),
            'pattern': 'regular'  # Could add more sophisticated analysis
        }
    
    def generate_weekly_seed(self) -> int:
        """Generate consistent but random seed for the week."""
        week_id = self.get_week_identifier()
        # Hash the week ID to get consistent randomness
        hash_obj = hashlib.md5(week_id.encode())
        return int(hash_obj.hexdigest()[:8], 16)
    
    def generate_animal_prompt(self, sleep_analysis: Dict, seed: int) -> str:
        """Generate AI prompt for animal selection and description."""
        
        # Set random seed for consistent weekly results
        random.seed(seed)
        
        # Random elements to ensure variety
        animal_moods = ['playful', 'wise', 'adventurous', 'peaceful', 'curious', 'gentle', 'spirited', 'dreamy']
        animal_habitats = ['forest', 'ocean', 'mountain', 'meadow', 'desert', 'arctic', 'jungle', 'sky']
        sleep_metaphors = ['hibernation', 'nesting', 'moonlight rituals', 'dream journeys', 'stargazing', 'twilight adventures']
        
        mood = random.choice(animal_moods)
        habitat = random.choice(animal_habitats)
        metaphor = random.choice(sleep_metaphors)
        
        # Get personality influence
        personality_weight = float(self.config.get('sleep_animal', 'personality_weight', fallback='0.3'))
        
        prompt = f"""Create a unique weekly sleep spirit animal for someone with these sleep patterns:
- Average sleep: {sleep_analysis['avg_duration']} hours/night  
- Sleep consistency: {sleep_analysis['consistency']}
- Sleep quality: {sleep_analysis['quality']}
- Nights tracked: {sleep_analysis['nights_tracked']}

REQUIREMENTS:
1. Choose ONE specific animal (not generic like "big cat" - be specific like "Snow Leopard")
2. The animal should be {mood} and connected to {habitat} themes
3. Incorporate {metaphor} into the description
4. Make it encouraging and fun, not medical advice
5. Include 2-3 specific traits that relate to their sleep patterns
6. Keep description under 200 words
7. Avoid scary/negative animals

PERSONALITY INFLUENCE: {personality_weight * 100:.0f}% based on sleep patterns, {(1-personality_weight) * 100:.0f}% random surprise

Format response as JSON:
{{
  "animal": "Specific Animal Name",
  "title": "Short catchy title (e.g., 'The Moonlit Dreamer')", 
  "description": "2-3 sentences about why this animal represents their sleep this week, focusing on positive aspects and gentle encouragement",
  "traits": ["trait1", "trait2", "trait3"],
  "sleep_wisdom": "One sentence of gentle sleep advice from this animal"
}}

Make each week's animal completely different and surprising!"""
        
        return prompt
    
    def call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API for text generation."""
        self.debug_log("=== OPENAI API CALL ===")
        
        api_key = self.config.get('openai', 'api_key', fallback='')
        if not api_key or api_key == 'YOUR_OPENAI_API_KEY':
            self.debug_log("OpenAI API key not configured", "WARN")
            return None
            
        model = self.config.get('openai', 'model', fallback='gpt-4o-mini')
        temperature = float(self.config.get('openai', 'temperature', fallback='0.8'))
        max_tokens = int(self.config.get('openai', 'max_tokens', fallback='200'))
        
        self.debug_log(f"Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}")
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key[:10]}***',  # Masked for logging
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            self.debug_log(f"Request URL: https://api.openai.com/v1/chat/completions")
            self.debug_log(f"Request payload: {json.dumps(data, indent=2)}")
            self.save_debug_file(f"openai_prompt_{datetime.now().strftime('%H%M%S')}.txt", prompt)
            
            # Make actual request with real API key
            headers['Authorization'] = f'Bearer {api_key}'
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            self.debug_log(f"Response status: {response.status_code}")
            self.debug_log(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                self.debug_log(f"✅ OpenAI response received: {len(content)} characters")
                self.debug_log(f"Response content: {content[:200]}...")
                self.save_debug_file(f"openai_response_{datetime.now().strftime('%H%M%S')}.json", json.dumps(result, indent=2))
                return content
            else:
                error_text = response.text
                self.debug_log(f"❌ OpenAI API error: {response.status_code} - {error_text}", "ERROR")
                self.save_debug_file(f"openai_error_{datetime.now().strftime('%H%M%S')}.txt", f"Status: {response.status_code}\n\n{error_text}")
                return None
                
        except Exception as e:
            self.debug_log(f"❌ Exception calling OpenAI API: {e}", "ERROR")
            return None
    
    def call_anthropic_api(self, prompt: str) -> Optional[str]:
        """Call Anthropic Claude API for text generation."""
        api_key = self.config.get('anthropic', 'api_key', fallback='')
        if not api_key or api_key == 'YOUR_ANTHROPIC_API_KEY':
            return None
            
        model = self.config.get('anthropic', 'model', fallback='claude-3-haiku-20240307')
        temperature = float(self.config.get('anthropic', 'temperature', fallback='0.7'))
        max_tokens = int(self.config.get('anthropic', 'max_tokens', fallback='200'))
        
        try:
            headers = {
                'x-api-key': api_key,
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                'model': model,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': [{'role': 'user', 'content': prompt}]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                print(f"Anthropic API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error calling Anthropic API: {e}")
            return None
    
    def call_openrouter_api(self, prompt: str) -> Optional[str]:
        """Call OpenRouter API for text generation."""
        self.debug_log("=== OPENROUTER API CALL ===")
        
        api_key = self.config.get('openrouter', 'api_key', fallback='')
        if not api_key or api_key == 'YOUR_OPENROUTER_API_KEY':
            self.debug_log("OpenRouter API key not configured", "WARN")
            return None
            
        base_url = self.config.get('openrouter', 'base_url', fallback='https://openrouter.ai/api/v1')
        model = self.config.get('openrouter', 'model', fallback='anthropic/claude-3.5-sonnet')
        # Clean model name (remove inline comments)
        model = model.split('#')[0].strip()
        temperature = float(self.config.get('openrouter', 'temperature', fallback='0.8'))
        max_tokens = int(self.config.get('openrouter', 'max_tokens', fallback='200'))
        
        self.debug_log(f"Base URL: {base_url}")
        self.debug_log(f"Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}")
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/fitbit-importer',
                'X-Title': 'Fitbit Sleep Animals'
            }
            
            # For debug logging, mask the API key
            headers_for_log = headers.copy()
            headers_for_log['Authorization'] = f'Bearer {api_key[:10]}***'
            
            data = {
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            endpoint_url = f'{base_url}/chat/completions'
            self.debug_log(f"Request URL: {endpoint_url}")
            self.debug_log(f"Request headers: {json.dumps(headers_for_log, indent=2)}")
            self.debug_log(f"Request payload: {json.dumps(data, indent=2)}")
            self.save_debug_file(f"openrouter_prompt_{datetime.now().strftime('%H%M%S')}.txt", prompt)
            
            # Make actual request with real API key
            headers['Authorization'] = f'Bearer {api_key}'
            
            self.debug_log("🚀 Sending request to OpenRouter...")
            
            response = requests.post(
                endpoint_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            self.debug_log(f"Response status: {response.status_code}")
            self.debug_log(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                self.debug_log(f"✅ Raw OpenRouter response: {json.dumps(result, indent=2)}")
                
                # Check response structure
                if 'choices' in result and len(result['choices']) > 0:
                    if 'message' in result['choices'][0] and 'content' in result['choices'][0]['message']:
                        content = result['choices'][0]['message']['content']
                        self.debug_log(f"✅ OpenRouter response received: {len(content)} characters")
                        self.debug_log(f"Response content: {content[:200]}...")
                        self.save_debug_file(f"openrouter_response_{datetime.now().strftime('%H%M%S')}.json", json.dumps(result, indent=2))
                        return content
                    else:
                        self.debug_log(f"❌ Unexpected response structure - no content in message", "ERROR")
                        self.save_debug_file(f"openrouter_bad_structure_{datetime.now().strftime('%H%M%S')}.json", json.dumps(result, indent=2))
                        return None
                else:
                    self.debug_log(f"❌ Unexpected response structure - no choices", "ERROR")
                    self.save_debug_file(f"openrouter_no_choices_{datetime.now().strftime('%H%M%S')}.json", json.dumps(result, indent=2))
                    return None
            else:
                error_text = response.text
                self.debug_log(f"❌ OpenRouter API error: {response.status_code} - {error_text}", "ERROR")
                self.save_debug_file(f"openrouter_error_{datetime.now().strftime('%H%M%S')}.txt", f"Status: {response.status_code}\n\n{error_text}")
                
                # Try to parse error details
                try:
                    error_json = response.json()
                    if 'error' in error_json:
                        self.debug_log(f"Error details: {json.dumps(error_json['error'], indent=2)}", "ERROR")
                except:
                    pass
                    
                return None
                
        except Exception as e:
            self.debug_log(f"❌ Exception calling OpenRouter API: {e}", "ERROR")
            import traceback
            self.debug_log(f"Full traceback: {traceback.format_exc()}", "ERROR")
            return None
    
    def generate_animal_description(self, sleep_analysis: Dict) -> Optional[Dict]:
        """Generate animal description using AI."""
        self.debug_log("🎲 Starting AI animal generation...")
        
        if not self.is_configured():
            self.debug_log("❌ AI not configured, returning None", "WARN")
            return None
            
        seed = self.generate_weekly_seed()
        self.debug_log(f"Weekly seed: {seed}")
        
        prompt = self.generate_animal_prompt(sleep_analysis, seed)
        self.debug_log(f"Generated prompt ({len(prompt)} chars)")
        
        # Try OpenRouter first, then OpenAI, then Anthropic
        self.debug_log("Attempting OpenRouter API...")
        response = self.call_openrouter_api(prompt)
        if not response:
            self.debug_log("OpenRouter failed, trying OpenAI API...")
            response = self.call_openai_api(prompt)
        if not response:
            self.debug_log("OpenAI failed, trying Anthropic API...")
            response = self.call_anthropic_api(prompt)
        
        if not response:
            return None
        
        # Parse JSON response
        try:
            # Extract JSON from response (in case there's extra text)
            import re
            json_match = re.search(r'\\{.*\\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(response)
        except:
            # Fallback if JSON parsing fails
            return {
                'animal': 'Wise Owl',
                'title': 'The Night Guardian',
                'description': response[:200] + '...' if len(response) > 200 else response,
                'traits': ['Nocturnal wisdom', 'Peaceful rest', 'Gentle guidance'],
                'sleep_wisdom': 'Rest comes to those who embrace the quiet of night.'
            }
    
    def generate_weekly_animal(self, sleep_data=None) -> Dict:
        """Generate this week's sleep animal."""
        self.debug_log("🦌 Starting weekly animal generation...")
        
        # Check cache first
        cached = self.get_cached_animal()
        if cached:
            self.debug_log("📋 Found cached animal, using it")
            return cached
        
        self.debug_log("📊 No cache found, generating new animal")
        
        # Analyze sleep patterns
        sleep_analysis = self.analyze_sleep_patterns(sleep_data)
        self.debug_log(f"Sleep analysis completed: {len(sleep_analysis)} data points")
        
        # Generate AI description
        is_config = self.is_configured()
        self.debug_log(f"Configuration check: {is_config}")
        
        if is_config:
            self.debug_log("🤖 Calling AI generation...")
            animal_data = self.generate_animal_description(sleep_analysis)
            self.debug_log(f"AI generation result: {animal_data is not None}")
            
            # Generate images if AI description was successful
            if animal_data:
                self.debug_log("🎨 Attempting to generate animal images...")
                image_results = self.generate_animal_image(animal_data)
                if isinstance(image_results, dict):
                    # Add both images to the animal data
                    animal_data['image_urls'] = image_results
                    if image_results.get('xai'):
                        self.debug_log("✅ XAI image added to animal data")
                    if image_results.get('openrouter'):
                        self.debug_log("✅ OpenRouter image added to animal data")
                    if image_results.get('nanobanana'):
                        self.debug_log("✅ Nano Banana image added to animal data")
                    
                    # Keep backwards compatibility with single image_url
                    if image_results.get('openrouter'):
                        animal_data['image_url'] = image_results['openrouter']
                    elif image_results.get('xai'):
                        animal_data['image_url'] = image_results['xai']
                else:
                    self.debug_log("ℹ️ No images generated, continuing without images")
        else:
            self.debug_log("❌ AI not configured, skipping generation")
            animal_data = None
        
        # Fallback if AI fails
        if not animal_data:
            seed = self.generate_weekly_seed()
            random.seed(seed)
            
            fallback_animals = [
                {
                    'animal': 'Sleepy Koala',
                    'title': 'The Dream Hugger',
                    'description': 'Like a koala who sleeps 20 hours a day, you understand the art of rest. Your sleep patterns show dedication to recharging your spirit.',
                    'traits': ['Deep sleeper', 'Rest enthusiast', 'Dream collector'],
                    'sleep_wisdom': 'Quality rest is the foundation of a vibrant life.'
                },
                {
                    'animal': 'Night Owl',
                    'title': 'The Moonlight Scholar',
                    'description': 'Wise and observant, you navigate the night with grace. Your sleep rhythms dance to their own beautiful melody.',
                    'traits': ['Night wisdom', 'Independent spirit', 'Peaceful observer'],
                    'sleep_wisdom': 'Honor your natural rhythms and rest will find you.'
                }
            ]
            animal_data = random.choice(fallback_animals)
        
        # Add metadata
        animal_data.update({
            'generated_date': datetime.now().isoformat(),
            'week_id': self.get_week_identifier(),
            'sleep_analysis': sleep_analysis
        })
        
        # Note: Image generation happens earlier if AI is configured
                
        # Cache the result
        self.cache_animal(animal_data)
        
        return animal_data
    
    def load_demo_images(self) -> Dict[str, Optional[str]]:
        """Load saved images from disk for demonstration purposes."""
        import base64
        from pathlib import Path
        
        results = {"xai": None, "openrouter": None}
        
        try:
            # Look for the most recent XAI image
            images_dir = Path('sleep_animal_images')
            if images_dir.exists():
                xai_images = list(images_dir.glob('sleep_animal_xai_*.png'))
                if xai_images:
                    # Get the most recent XAI image
                    latest_xai = max(xai_images, key=lambda x: x.stat().st_mtime)
                    with open(latest_xai, 'rb') as f:
                        xai_data = base64.b64encode(f.read()).decode()
                        results["xai"] = f"data:image/png;base64,{xai_data}"
                        self.debug_log(f"Loaded demo XAI image: {latest_xai}")
                
                # Look for the most recent OpenRouter image
                openrouter_images = list(images_dir.glob('sleep_animal_openrouter_*.png'))
                if openrouter_images:
                    latest_openrouter = max(openrouter_images, key=lambda x: x.stat().st_mtime)
                    with open(latest_openrouter, 'rb') as f:
                        openrouter_data = base64.b64encode(f.read()).decode()
                        results["openrouter"] = f"data:image/png;base64,{openrouter_data}"
                        self.debug_log(f"Loaded demo OpenRouter image: {latest_openrouter}")
                        
        except Exception as e:
            self.debug_log(f"Could not load demo images: {e}", "ERROR")
            
        return results


    def generate_animal_image(self, animal_data: Dict) -> Dict[str, Optional[str]]:
        """Generate an image for the sleep animal using XAI via OpenRouter."""
        if not self.is_configured():
            self.debug_log("AI not configured for image generation", "WARN")
            return {"xai": None, "openrouter": None}
            
        # Check if image generation is enabled
        include_image = self.config.getboolean('sleep_animal', 'include_image', fallback=True) if self.config else True
        if not include_image:
            self.debug_log("Image generation disabled in config", "INFO")
            return {"xai": None, "openrouter": None}
            
        try:
            self.debug_log("🎨 Starting DALL-E image generation via OpenRouter...")
            
            # Create artistic prompt for the animal
            animal_name = animal_data.get('animal', 'mystical creature')
            title = animal_data.get('title', '')
            description = animal_data.get('description', '')
            
            self.debug_log(f"🎨 Animal name for image: '{animal_name}'")
            
            # Create an artistic prompt focusing on sleep/dream themes
            image_prompt = f"""Create a dreamy, whimsical illustration of a {animal_name} in a peaceful sleep setting. 
Style: soft watercolor illustration with ethereal lighting
Scene: The {animal_name} should be in a serene forest clearing under moonlight, surrounded by gentle glowing elements like fireflies or soft starlight
Mood: peaceful, magical, dreamy
Colors: soft pastels with touches of silver and blue moonlight
Details: Include subtle sleep-themed elements like floating dream bubbles, soft clouds, or gentle mist
Avoid: scary, dark, or aggressive elements - keep it peaceful and encouraging"""
            
            self.debug_log(f"Generated image prompt ({len(image_prompt)} chars)")
            
            # Try XAI, OpenRouter, and Nano Banana to get all images
            results = {}
            
            self.debug_log("Attempting XAI image generation...")
            results["xai"] = self.call_xai_image_api(image_prompt)
            
            self.debug_log("Attempting OpenRouter image generation...")
            results["openrouter"] = self.call_openrouter_image_api(image_prompt)
            
            self.debug_log("Attempting Nano Banana (Google AI) image generation...")
            results["nanobanana"] = self.call_nanobanana_image_api(image_prompt)
            
            # Return all results for comparison
            if results["xai"] or results["openrouter"] or results["nanobanana"]:
                self.debug_log(f"✅ Image generation results: XAI={bool(results['xai'])}, OpenRouter={bool(results['openrouter'])}, NanoBanana={bool(results['nanobanana'])}")
                return results
            else:
                self.debug_log("❌ All image generation methods failed", "ERROR")
                return {"xai": None, "openrouter": None, "nanobanana": None}
                
        except Exception as e:
            self.debug_log(f"Image generation error: {str(e)}", "ERROR")
            return {"xai": None, "openrouter": None, "nanobanana": None}
    
    def call_xai_image_api(self, prompt: str) -> Optional[str]:
        """Call XAI API directly for image generation."""
        self.debug_log("=== XAI DIRECT API CALL ===")
        
        api_key = self.config.get('xai', 'api_key', fallback='')
        if not api_key or api_key == 'YOUR_XAI_API_KEY':
            self.debug_log("XAI API key not configured", "WARN")
            return None
            
        base_url = self.config.get('xai', 'base_url', fallback='https://api.x.ai/v1')
        model = self.config.get('xai', 'model', fallback='grok-2-image-1212')
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # For debug logging, mask the API key
            headers_for_log = headers.copy()
            headers_for_log['Authorization'] = f'Bearer {api_key[:10]}***'
            
            # XAI API format for image generation
            data = {
                'model': model,
                'prompt': prompt,
                'response_format': 'b64_json'
            }
            
            endpoint_url = f'{base_url}/images/generations'
            self.debug_log(f"Request URL: {endpoint_url}")
            self.debug_log(f"Request headers: {json.dumps(headers_for_log, indent=2)}")
            self.debug_log(f"Request payload: {json.dumps(data, indent=2)}")
            self.save_debug_file(f"xai_image_prompt_{datetime.now().strftime('%H%M%S')}.txt", prompt)
            
            self.debug_log(f"🚀 Sending image request to XAI direct API...")
            response = requests.post(endpoint_url, json=data, headers=headers, timeout=60)
            
            self.debug_log(f"Response status: {response.status_code}")
            self.debug_log(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                self.debug_log(f"✅ XAI image generation successful")
                self.save_debug_file(f"xai_image_success_{datetime.now().strftime('%H%M%S')}.json", json.dumps(result, indent=2))
                
                # Extract image from XAI response - check for 'data' array with image data
                if 'data' in result and len(result['data']) > 0:
                    image_item = result['data'][0]
                    
                    # Check for b64_json format
                    if 'b64_json' in image_item:
                        image_data = image_item['b64_json']
                        image_url = f"data:image/png;base64,{image_data}"
                        self.debug_log(f"Found b64_json image data")
                        
                        # Save image to file
                        saved_path = self.save_image_to_file(image_url, 'xai')
                        if saved_path:
                            self.debug_log(f"💾 Saved XAI image to: {saved_path}")
                        
                        return image_url
                    
                    # Check for URL format
                    elif 'url' in image_item:
                        image_url = image_item['url']
                        self.debug_log(f"Found image URL: {image_url}")
                        return image_url
                        
                self.debug_log("No image found in XAI response", "WARN")
                return None
            else:
                error_text = response.text
                self.debug_log(f"❌ XAI API error: {response.status_code} - {error_text}", "ERROR")
                self.save_debug_file(f"xai_image_error_{datetime.now().strftime('%H%M%S')}.txt", error_text)
                
                try:
                    error_data = response.json()
                    self.debug_log(f"Error details: {json.dumps(error_data, indent=2)}", "ERROR")
                except:
                    pass
                    
                return None
                
        except requests.exceptions.RequestException as e:
            self.debug_log(f"XAI API request failed: {str(e)}", "ERROR")
            return None
        except Exception as e:
            self.debug_log(f"XAI API unexpected error: {str(e)}", "ERROR")
            return None

    def call_openrouter_image_api(self, prompt: str) -> Optional[str]:
        """Call image generation through OpenRouter API using proper format."""
        self.debug_log("=== OPENROUTER IMAGE GENERATION ===")
        
        api_key = self.config.get('openrouter', 'api_key', fallback='')
        if not api_key or api_key == 'YOUR_OPENROUTER_API_KEY':
            self.debug_log("OpenRouter API key not configured", "WARN")
            return None
            
        base_url = self.config.get('openrouter', 'base_url', fallback='https://openrouter.ai/api/v1')
        
        # Try image generation models actually available through OpenRouter
        image_models = [
            "google/gemini-2.5-flash-image-preview",  # OpenRouter's first image generation model (just launched!)
        ]
        
        for image_model in image_models:
            self.debug_log(f"Trying image model: {image_model}")
            
            try:
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                    'HTTP-Referer': 'https://github.com/fitbit-importer',
                    'X-Title': 'Fitbit Sleep Animals'
                }
                
                # For debug logging, mask the API key
                headers_for_log = headers.copy()
                headers_for_log['Authorization'] = f'Bearer {api_key[:10]}***'
                
                # Use OpenRouter's correct format for image generation
                data = {
                    'model': image_model,
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'modalities': ['image', 'text']
                }
                
                endpoint_url = f'{base_url}/chat/completions'
                self.debug_log(f"Request URL: {endpoint_url}")
                self.debug_log(f"Request headers: {json.dumps(headers_for_log, indent=2)}")
                self.debug_log(f"Request payload: {json.dumps(data, indent=2)}")
                self.save_debug_file(f"openrouter_image_prompt_{datetime.now().strftime('%H%M%S')}.txt", prompt)
                
                self.debug_log(f"🚀 Sending image request to OpenRouter with {image_model}...")
                response = requests.post(endpoint_url, json=data, headers=headers, timeout=60)
                
                self.debug_log(f"Response status: {response.status_code}")
                self.debug_log(f"Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    result = response.json()
                    self.debug_log(f"✅ OpenRouter image generation successful with {image_model}")
                    self.save_debug_file(f"openrouter_image_success_{datetime.now().strftime('%H%M%S')}.json", json.dumps(result, indent=2))
                    
                    # Extract image from response - OpenRouter returns base64 in message.images
                    if 'choices' in result and len(result['choices']) > 0:
                        message = result['choices'][0].get('message', {})
                        
                        # Check for images in the response
                        if 'images' in message and len(message['images']) > 0:
                            # OpenRouter returns images in a structured format
                            image_item = message['images'][0]
                            self.debug_log(f"Found image item: {type(image_item)} - {str(image_item)[:100]}...")
                            
                            # Extract the actual base64 data
                            if isinstance(image_item, dict) and 'image_url' in image_item:
                                image_url = image_item['image_url']['url']
                                self.debug_log(f"Found nested image URL: {len(image_url)} chars")
                                
                                # Save image to file
                                saved_path = self.save_image_to_file(image_url, 'openrouter')
                                if saved_path:
                                    self.debug_log(f"💾 Saved OpenRouter image to: {saved_path}")
                                
                                return image_url
                            elif isinstance(image_item, str):
                                # Direct base64 string
                                image_url = f"data:image/png;base64,{image_item}"
                                self.debug_log(f"Found direct base64 image data ({len(image_item)} chars)")
                                
                                # Save image to file
                                saved_path = self.save_image_to_file(image_url, 'openrouter')
                                if saved_path:
                                    self.debug_log(f"💾 Saved OpenRouter image to: {saved_path}")
                                
                                return image_url
                            
                        self.debug_log("No images found in response", "WARN")
                        
                    self.debug_log("No valid response structure found", "ERROR")
                    continue  # Try next model
                else:
                    error_text = response.text
                    self.debug_log(f"❌ OpenRouter API error with {image_model}: {response.status_code} - {error_text}", "ERROR")
                    self.save_debug_file(f"openrouter_image_error_{datetime.now().strftime('%H%M%S')}.txt", error_text)
                    
                    try:
                        error_data = response.json()
                        self.debug_log(f"Error details: {json.dumps(error_data, indent=2)}", "ERROR")
                    except:
                        pass
                    
                    # If it's a model not found error, try the next model
                    if response.status_code in [400, 404]:
                        continue  # Try next model
                    else:
                        return None  # Different error, don't try more models
                        
            except requests.exceptions.RequestException as e:
                self.debug_log(f"OpenRouter image API request failed with {image_model}: {str(e)}", "ERROR")
                continue  # Try next model
            except Exception as e:
                self.debug_log(f"OpenRouter image API unexpected error with {image_model}: {str(e)}", "ERROR")
                continue  # Try next model
        
        self.debug_log("All image models failed", "ERROR")
        return None

    def call_nanobanana_image_api(self, prompt: str) -> Optional[str]:
        """Call Google AI (Nano Banana/Gemini 2.5 Flash Image Preview) for image generation."""
        self.debug_log("=== NANO BANANA (GOOGLE AI) API CALL ===")
        
        api_key = self.config.get('google_ai', 'api_key', fallback='')
        if not api_key or api_key == 'YOUR_GOOGLE_AI_API_KEY':
            self.debug_log("Google AI API key not configured", "WARN")
            return None
            
        base_url = self.config.get('google_ai', 'base_url', fallback='https://generativelanguage.googleapis.com/v1beta')
        model = self.config.get('google_ai', 'model', fallback='gemini-2.5-flash-image-preview')
        
        try:
            headers = {
                'x-goog-api-key': api_key,
                'Content-Type': 'application/json'
            }
            
            # For debug logging, mask the API key
            headers_for_log = headers.copy()
            headers_for_log['x-goog-api-key'] = f'{api_key[:10]}***'
            
            # Google AI API format for image generation
            data = {
                'contents': [
                    {
                        'parts': [
                            {
                                'text': prompt
                            }
                        ]
                    }
                ]
            }
            
            endpoint_url = f'{base_url}/models/{model}:generateContent'
            self.debug_log(f"Request URL: {endpoint_url}")
            self.debug_log(f"Request headers: {json.dumps(headers_for_log, indent=2)}")
            self.debug_log(f"Request payload: {json.dumps(data, indent=2)}")
            self.save_debug_file(f"nanobanana_image_prompt_{datetime.now().strftime('%H%M%S')}.txt", prompt)
            
            self.debug_log(f"🚀 Sending image request to Nano Banana (Google AI)...")
            response = requests.post(endpoint_url, json=data, headers=headers, timeout=60)
            
            self.debug_log(f"Response status: {response.status_code}")
            self.debug_log(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                self.debug_log(f"✅ Nano Banana image generation successful")
                self.save_debug_file(f"nanobanana_image_success_{datetime.now().strftime('%H%M%S')}.json", json.dumps(result, indent=2))
                
                # Extract image from Google AI response
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        
                        for part in parts:
                            # Look for inline_data containing image data
                            if 'inlineData' in part:
                                inline_data = part['inlineData']
                                if 'data' in inline_data:
                                    image_data = inline_data['data']
                                    mime_type = inline_data.get('mimeType', 'image/png')
                                    image_url = f"data:{mime_type};base64,{image_data}"
                                    self.debug_log(f"Found inline image data ({len(image_data)} chars)")
                                    
                                    # Save image to file
                                    saved_path = self.save_image_to_file(image_url, 'nanobanana')
                                    if saved_path:
                                        self.debug_log(f"💾 Saved Nano Banana image to: {saved_path}")
                                    
                                    return image_url
                
                self.debug_log("No image found in Nano Banana response", "WARN")
                return None
            else:
                error_text = response.text
                self.debug_log(f"❌ Nano Banana API error: {response.status_code} - {error_text}", "ERROR")
                self.save_debug_file(f"nanobanana_image_error_{datetime.now().strftime('%H%M%S')}.txt", error_text)
                
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        self.debug_log(f"Error details: {json.dumps(error_data['error'], indent=2)}", "ERROR")
                except:
                    pass
                
                return None
                
        except Exception as e:
            self.debug_log(f"❌ Exception calling Nano Banana API: {e}", "ERROR")
            import traceback
            self.debug_log(f"Full traceback: {traceback.format_exc()}", "ERROR")
            return None


def test_sleep_animal_generator():
    """Test the sleep animal generator."""
    generator = SleepAnimalGenerator()
    
    # Mock sleep data
    mock_sleep_data = [
        {'hoursAsleep': 7.5, 'date': '2025-09-01'},
        {'hoursAsleep': 8.0, 'date': '2025-09-02'},
        {'hoursAsleep': 6.5, 'date': '2025-09-03'},
        {'hoursAsleep': 7.8, 'date': '2025-09-04'},
        {'hoursAsleep': 8.2, 'date': '2025-09-05'}
    ]
    
    print("🐾 Testing Sleep Animal Generator")
    print("=" * 40)
    
    if not generator.is_configured():
        print("⚠️ AI not configured, will use fallback animals")
    
    animal = generator.generate_weekly_animal(mock_sleep_data)
    
    print(f"🦊 Animal: {animal['animal']}")
    print(f"👑 Title: {animal['title']}")
    print(f"📝 Description: {animal['description']}")
    print(f"✨ Traits: {', '.join(animal['traits'])}")
    print(f"💭 Wisdom: {animal['sleep_wisdom']}")
    
    return animal


if __name__ == "__main__":
    test_sleep_animal_generator()