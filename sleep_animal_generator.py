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
        
        # Cache directory for generated animals
        self.cache_dir = Path('sleep_animals_cache')
        self.cache_dir.mkdir(exist_ok=True)
        
    def is_configured(self) -> bool:
        """Check if AI services are properly configured."""
        if not self.config:
            return False
            
        # Check if we have at least one text generation API configured
        openai_key = self.config.get('openai', 'api_key', fallback='').strip()
        anthropic_key = self.config.get('anthropic', 'api_key', fallback='').strip()
        
        has_text_api = (openai_key and openai_key != 'YOUR_OPENAI_API_KEY') or \
                      (anthropic_key and anthropic_key != 'YOUR_ANTHROPIC_API_KEY')
        
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
        if not sleep_data or len(sleep_data) == 0:
            return {
                'avg_duration': 7.5,
                'consistency': 'unknown',
                'quality': 'moderate',
                'pattern': 'regular'
            }
        
        # Calculate basic metrics
        durations = [row.get('hoursAsleep', 7.5) for row in sleep_data if row.get('hoursAsleep')]
        avg_duration = sum(durations) / len(durations) if durations else 7.5
        
        # Determine patterns
        consistency = 'consistent' if len(set(durations)) <= 3 else 'variable'
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
        
        prompt = f\"\"\"Create a unique weekly sleep spirit animal for someone with these sleep patterns:
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

Make each week's animal completely different and surprising!\"\"\"
        
        return prompt
    
    def call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API for text generation."""
        api_key = self.config.get('openai', 'api_key', fallback='')
        if not api_key or api_key == 'YOUR_OPENAI_API_KEY':
            return None
            
        model = self.config.get('openai', 'model', fallback='gpt-4o-mini')
        temperature = float(self.config.get('openai', 'temperature', fallback='0.8'))
        max_tokens = int(self.config.get('openai', 'max_tokens', fallback='200'))
        
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
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
    
    def generate_animal_description(self, sleep_analysis: Dict) -> Optional[Dict]:
        """Generate animal description using AI."""
        if not self.is_configured():
            return None
            
        seed = self.generate_weekly_seed()
        prompt = self.generate_animal_prompt(sleep_analysis, seed)
        
        # Try OpenAI first, then Anthropic
        response = self.call_openai_api(prompt)
        if not response:
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
        
        # Check cache first
        cached = self.get_cached_animal()
        if cached:
            return cached
        
        # Analyze sleep patterns
        sleep_analysis = self.analyze_sleep_patterns(sleep_data)
        
        # Generate AI description
        if self.is_configured():
            animal_data = self.generate_animal_description(sleep_analysis)
        else:
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
        
        # Cache the result
        self.cache_animal(animal_data)
        
        return animal_data


def test_sleep_animal_generator():
    \"\"\"Test the sleep animal generator.\"\"\"
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