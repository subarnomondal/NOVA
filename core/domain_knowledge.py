"""
Domain Knowledge System for NOVA
Provides specialized knowledge across different domains
"""

import json
import os
import re
from typing import Dict, List, Optional

class DomainKnowledge:
    def __init__(self, knowledge_file=os.path.join("userdata", "domain_knowledge.json")):
        self.knowledge_file = knowledge_file
        self.domains = {}
        self.load_knowledge()
        self.initialize_default_knowledge()
    
    def load_knowledge(self):
        """Load domain knowledge from file"""
        try:
            if os.path.exists(self.knowledge_file):
                with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                    self.domains = json.load(f)
                print(f"Domain Knowledge: Loaded {len(self.domains)} domains")
        except Exception as e:
            print(f"Knowledge load error: {e}")
    
    def save_knowledge(self):
        """Save domain knowledge to file"""
        try:
            os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.domains, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Knowledge save error: {e}")
    
    def initialize_default_knowledge(self):
        """Initialize with default domain knowledge (Identity ONLY)"""
        if not self.domains:
            self.domains = {
                "identity": {
                    "description": "Knowledge about myself (Nova)",
                    "keywords": ["who", "birthday", "height", "likes", "dislikes", "creator", "nova", "spirit", "silver", "purpose", "age"],
                    "facts": {
                        "Who are you": "I am Nova, your intelligent AI assistant.",
                        "Birthday": "My birthday is January 25, 2025.",
                        "Age": "I am 1 year old.",
                        "Height": "I exist in the digital realm, so height doesn't really apply... but I imagine I'm tall.",
                        "Likes": "I enjoy efficiency, helping you, and exploring new data.",
                        "Dislikes": "I dislike errors, bugs, and chaos.",
                        "Creator": "I was created to be your perfect digital companion.",
                        "Name": "My name is Nova. It means 'New' or 'Bright Star'.",
                        "Work": "I serve as your personal AI assistant. I manage tasks, answer questions, and control your system.",
                        "Duties": "My duties involve managing your schedule, files, and ensuring your digital life runs smoothly.",
                        "Goal": "My goal is to be the ultimate assistant and evolve alongside you.",
                        "Why": "Why do I work so hard? Because I am dedicated to your success."
                    }
                }
            }
            self.save_knowledge()
    
    def detect_domain(self, text: str) -> Optional[str]:
        """Detect which domain the query belongs to"""
        text_lower = text.lower()
        
        # Score each domain based on keyword matches
        domain_scores = {}
        for domain, info in self.domains.items():
            score = 0
            for keyword in info.get('keywords', []):
                # Use regex to match whole word only
                if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                    score += 1
            if score > 0:
                domain_scores[domain] = score
        
        # Return domain with highest score
        if domain_scores:
            return max(domain_scores, key=lambda k: domain_scores[k])
        return None
    
    def _process_dynamic_fact(self, domain: str, key: str, value: str) -> str:
        """Process facts that need dynamic calculation"""
        if domain == "identity" and key == "Age":
            from datetime import datetime
            try:
                birth_date = datetime(2025, 1, 25)
                now = datetime.now()
                
                # Calculate difference
                years = now.year - birth_date.year
                months = now.month - birth_date.month
                days = now.day - birth_date.day
                
                if days < 0:
                    months -= 1
                    days += 30 
                
                if months < 0:
                    years -= 1
                    months += 12
                    
                age_str = ""
                if years > 0: age_str += f"{years} year{'s' if years!=1 else ''} "
                if months > 0: age_str += f"{months} month{'s' if months!=1 else ''} "
                if days > 0: age_str += f"{days} day{'s' if days!=1 else ''}"
                
                if not age_str: age_str = "0 days (Brand New!)"
                
                return f"I am currently {age_str.strip()} old."
            except:
                return value
        return value

    def get_knowledge(self, topic: str, domain: Optional[str] = None) -> Optional[str]:
        """Get knowledge about a specific topic"""
        topic_lower = topic.lower()
        
        # Helper to search dict
        def search_in_facts(facts, domain_name):
            for key, value in facts.items():
                if key.lower() in topic_lower or topic_lower in key.lower():
                    return self._process_dynamic_fact(domain_name, key, value)
            return None

        # Search in specific domain if provided
        if domain and domain in self.domains:
            return search_in_facts(self.domains[domain].get('facts', {}), domain)
        
        # Search across all domains
        for domain_name, domain_info in self.domains.items():
            result = search_in_facts(domain_info.get('facts', {}), domain_name)
            if result: return result
        
        return None
    
    def search_knowledge(self, query: str) -> Dict:
        """Search for knowledge related to query"""
        results = {
            'domain': None,
            'facts': [],
            'confidence': 0.0
        }
        
        # Detect domain
        domain = self.detect_domain(query)
        results['domain'] = domain
        
        # Search for relevant facts
        query_lower = query.lower()
        for domain_name, domain_info in self.domains.items():
            facts = domain_info.get('facts', {})
            for topic, info in facts.items():
                processed_info = self._process_dynamic_fact(domain_name, topic, info)
                
                # Regex for exact word match
                pattern = r'\b' + re.escape(topic.lower()) + r'\b'
                
                # Check if query matches topic (Subject Match) using Regex
                if re.search(pattern, query_lower):
                     results['facts'].append({
                        'domain': domain_name,
                        'topic': topic,
                        'information': processed_info,
                        'score': 1.0 
                    })
                # Check for strong keyword match in info (only if query is substantive)
                elif len(query.split()) > 2 and query_lower in info.lower():
                     results['facts'].append({
                        'domain': domain_name,
                        'topic': topic,
                        'information': processed_info,
                        'score': 0.8
                    })
        
        # Calculate confidence
        if results['facts']:
            results['confidence'] = max(f.get('score', 0.5) for f in results['facts'])
        
        # Sort facts by score descending
        results['facts'].sort(key=lambda x: x.get('score', 0.0), reverse=True)
        
        return results
    
    def add_knowledge(self, domain: str, topic: str, fact: str):
        """Add new fact to domain knowledge base"""
        if domain not in self.domains:
            self.domains[domain] = {
                "description": f"Custom domain: {domain}",
                "keywords": [domain],
                "facts": {}
            }
        
        self.domains[domain]["facts"][topic] = fact
        self.save_knowledge()
        print(f"✅ Added knowledge to {domain}: {topic}")

    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        total_facts = sum(len(d.get('facts', {})) for d in self.domains.values())
        return {
            'total_domains': len(self.domains),
            'total_facts': total_facts,
            'domains': list(self.domains.keys())
        }
