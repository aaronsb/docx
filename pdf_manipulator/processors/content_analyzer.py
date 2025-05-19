"""Content analyzer for initial lexical analysis."""
import re
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
import logging

import nltk
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords


@dataclass
class WordStem:
    """Represents a word stem with frequency information."""
    stem: str
    original_words: Set[str] = field(default_factory=set)
    frequency: int = 0
    tf_idf_score: float = 0.0
    
    def add_word(self, word: str):
        """Add an original word to this stem."""
        self.original_words.add(word)
        self.frequency += 1


@dataclass
class Term:
    """Represents a significant term with contextual information."""
    text: str
    stem: str
    frequency: int
    significance: float
    contexts: List[str] = field(default_factory=list)
    related_terms: Set[str] = field(default_factory=set)


@dataclass
class Relationship:
    """Represents a relationship between concepts."""
    source: str
    target: str
    type: str  # co-occurrence, synonym, part_of, etc.
    strength: float
    evidence: List[str] = field(default_factory=list)


class ContentAnalyzer:
    """Performs initial content analysis without deep LLM processing."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the content analyzer."""
        self.logger = logger or logging.getLogger(__name__)
        self.stemmer = PorterStemmer()
        
        # Download required NLTK data if not available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
        
        self.stop_words = set(stopwords.words('english'))
        
        # Common domain-specific stop words to exclude
        self.domain_stop_words = {
            'page', 'figure', 'table', 'chapter', 'section',
            'example', 'note', 'see', 'also', 'above', 'below'
        }
        self.stop_words.update(self.domain_stop_words)
        
        # Relationship indicators
        self.relationship_indicators = {
            'is a': 'type_of',
            'is an': 'type_of',
            'are': 'type_of',
            'includes': 'contains',
            'contains': 'contains',
            'consists of': 'contains',
            'part of': 'part_of',
            'related to': 'relates_to',
            'similar to': 'similar_to',
            'such as': 'example_of',
            'for example': 'example_of',
            'e.g.': 'example_of',
            'i.e.': 'definition',
            'means': 'definition',
            'refers to': 'references',
            'see': 'references',
        }
    
    def extract_word_stems(self, text: str) -> List[WordStem]:
        """Extract word stems for indexing and frequency analysis."""
        # Tokenize and clean text
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        
        # Create stem mapping
        stem_map = defaultdict(WordStem)
        
        for word in words:
            stem = self.stemmer.stem(word)
            if stem not in stem_map:
                stem_map[stem] = WordStem(stem=stem)
            stem_map[stem].add_word(word)
        
        # Convert to list and sort by frequency
        stems = list(stem_map.values())
        stems.sort(key=lambda x: x.frequency, reverse=True)
        
        return stems
    
    def bayesian_analysis(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, float]:
        """Calculate term significance using Bayesian methods."""
        # Extract terms
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        
        # Calculate basic term frequencies
        term_freq = Counter(words)
        total_terms = sum(term_freq.values())
        
        # Calculate prior probabilities (can be enhanced with domain knowledge)
        priors = {}
        if context and 'domain_terms' in context:
            # Use domain-specific priors if available
            domain_terms = context['domain_terms']
            for term in term_freq:
                if term in domain_terms:
                    priors[term] = domain_terms[term]
                else:
                    priors[term] = 0.1  # Default prior
        else:
            # Uniform priors
            for term in term_freq:
                priors[term] = 0.5
        
        # Calculate posterior probabilities (term significance)
        significance = {}
        
        for term, freq in term_freq.items():
            # Term probability in document
            p_term_doc = freq / total_terms
            
            # Prior probability
            p_term = priors.get(term, 0.5)
            
            # Document probability (simplified)
            p_doc = 1.0
            
            # Bayesian update
            p_doc_term = (p_term_doc * p_doc) / p_term if p_term > 0 else 0
            
            # Significance score (combines frequency and Bayesian probability)
            significance[term] = p_term_doc * p_doc_term * math.log(freq + 1)
        
        return significance
    
    def detect_relationships(self, text: str) -> List[Relationship]:
        """Find basic relationships between concepts using patterns."""
        relationships = []
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            # Look for relationship indicators
            for indicator, rel_type in self.relationship_indicators.items():
                if indicator in sentence.lower():
                    # Extract entities around the indicator
                    parts = sentence.lower().split(indicator)
                    if len(parts) >= 2:
                        source = self._extract_entity(parts[0])
                        target = self._extract_entity(parts[1])
                        
                        if source and target:
                            relationship = Relationship(
                                source=source,
                                target=target,
                                type=rel_type,
                                strength=0.7,  # Default strength
                                evidence=[sentence]
                            )
                            relationships.append(relationship)
            
            # Detect co-occurrence relationships
            entities = self._extract_all_entities(sentence)
            if len(entities) >= 2:
                # Create co-occurrence relationships for entities in same sentence
                for i, entity1 in enumerate(entities):
                    for entity2 in entities[i+1:]:
                        relationship = Relationship(
                            source=entity1,
                            target=entity2,
                            type='co_occurrence',
                            strength=0.5,
                            evidence=[sentence]
                        )
                        relationships.append(relationship)
        
        # Merge similar relationships and boost strength
        merged = self._merge_relationships(relationships)
        
        return merged
    
    def analyze_content(self, text: str, toc_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Perform comprehensive content analysis."""
        # Extract word stems
        stems = self.extract_word_stems(text)
        
        # Perform Bayesian analysis
        significance_scores = self.bayesian_analysis(text, toc_context)
        
        # Detect relationships
        relationships = self.detect_relationships(text)
        
        # Calculate TF-IDF scores if document context is available
        if toc_context and 'document_freq' in toc_context:
            stems = self._calculate_tf_idf(stems, toc_context['document_freq'])
        
        # Extract key terms
        key_terms = self._extract_key_terms(text, significance_scores, stems)
        
        return {
            'word_stems': stems,
            'key_terms': key_terms,
            'relationships': relationships,
            'significance_scores': significance_scores,
            'summary_stats': {
                'total_stems': len(stems),
                'unique_terms': len(significance_scores),
                'relationships': len(relationships),
                'avg_significance': sum(significance_scores.values()) / len(significance_scores) if significance_scores else 0
            }
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitter (can be enhanced)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_entity(self, text: str) -> Optional[str]:
        """Extract entity from text fragment."""
        # Remove common words and clean
        words = word_tokenize(text.strip())
        words = [w for w in words if w not in self.stop_words and w.isalnum()]
        
        if words:
            # Return the most significant noun phrase (simplified)
            return ' '.join(words[-3:])  # Last few words often contain the entity
        return None
    
    def _extract_all_entities(self, text: str) -> List[str]:
        """Extract all potential entities from text."""
        entities = []
        
        # Simple noun phrase extraction (can be enhanced with POS tagging)
        words = word_tokenize(text.lower())
        
        # Look for capitalized words (proper nouns)
        tokens = word_tokenize(text)  # Original case
        for i, token in enumerate(tokens):
            if token[0].isupper() and token.lower() not in self.stop_words:
                # Check if part of a multi-word entity
                entity = [token]
                j = i + 1
                while j < len(tokens) and tokens[j][0].isupper():
                    entity.append(tokens[j])
                    j += 1
                entities.append(' '.join(entity))
        
        # Look for technical terms (contains numbers or special patterns)
        for word in words:
            if any(char.isdigit() for char in word) or '_' in word or '-' in word:
                entities.append(word)
        
        return list(set(entities))  # Remove duplicates
    
    def _merge_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Merge similar relationships and adjust strength."""
        merged = defaultdict(lambda: {'strength': 0, 'evidence': []})
        
        for rel in relationships:
            key = (rel.source, rel.target, rel.type)
            merged[key]['strength'] += rel.strength
            merged[key]['evidence'].extend(rel.evidence)
        
        # Create merged relationship list
        result = []
        for (source, target, rel_type), data in merged.items():
            # Normalize strength (cap at 1.0)
            strength = min(data['strength'], 1.0)
            
            relationship = Relationship(
                source=source,
                target=target,
                type=rel_type,
                strength=strength,
                evidence=list(set(data['evidence']))  # Remove duplicate evidence
            )
            result.append(relationship)
        
        return result
    
    def _calculate_tf_idf(self, stems: List[WordStem], 
                         document_freq: Dict[str, int]) -> List[WordStem]:
        """Calculate TF-IDF scores for stems."""
        total_docs = document_freq.get('_total_docs', 1)
        
        for stem in stems:
            # Term frequency (already in stem.frequency)
            tf = stem.frequency
            
            # Inverse document frequency
            df = document_freq.get(stem.stem, 1)
            idf = math.log(total_docs / df) if df > 0 else 0
            
            # TF-IDF score
            stem.tf_idf_score = tf * idf
        
        # Re-sort by TF-IDF score
        stems.sort(key=lambda x: x.tf_idf_score, reverse=True)
        
        return stems
    
    def _extract_key_terms(self, text: str, significance_scores: Dict[str, float],
                          stems: List[WordStem]) -> List[Term]:
        """Extract key terms combining multiple signals."""
        terms = []
        
        # Create term mapping
        term_map = {}
        
        # Add terms from significance scores
        for term, score in significance_scores.items():
            if score > 0.1:  # Threshold for significance
                stem = self.stemmer.stem(term)
                term_obj = Term(
                    text=term,
                    stem=stem,
                    frequency=text.lower().count(term),
                    significance=score
                )
                term_map[term] = term_obj
        
        # Enhance with stem information
        for stem_obj in stems:
            for word in stem_obj.original_words:
                if word in term_map:
                    term_map[word].frequency = stem_obj.frequency
                    # Add related terms (other words with same stem)
                    term_map[word].related_terms.update(
                        stem_obj.original_words - {word}
                    )
        
        # Add context for top terms
        top_terms = sorted(term_map.values(), 
                          key=lambda x: x.significance, 
                          reverse=True)[:20]
        
        for term in top_terms:
            # Find sentences containing the term
            sentences = self._split_sentences(text)
            for sentence in sentences:
                if term.text in sentence.lower():
                    term.contexts.append(sentence)
        
        return top_terms