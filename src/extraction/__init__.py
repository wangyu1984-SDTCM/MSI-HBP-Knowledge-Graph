"""知识抽取模块"""
from .entity_extractor import EntityExtractor
from .relation_extractor import RelationExtractor
from .triple_generator import TripleGenerator

__all__ = ['EntityExtractor', 'RelationExtractor', 'TripleGenerator']
