"""External service clients (interfaces + stubs)."""
from libs.common.clients.serp import SerpProviderInterface, SerpResultItem, SerpStubClient
from libs.common.clients.llm import LLMClientInterface, LLMStubClient
from libs.common.clients.antiplagiat import AntiPlagiatInterface, AntiPlagiatStubClient
from libs.common.clients.tilda import TildaPublisherInterface, TildaStubClient
from libs.common.clients.indexer import IndexerInterface, IndexerStubClient

__all__ = [
    "SerpProviderInterface",
    "SerpResultItem",
    "SerpStubClient",
    "LLMClientInterface",
    "LLMStubClient",
    "AntiPlagiatInterface",
    "AntiPlagiatStubClient",
    "TildaPublisherInterface",
    "TildaStubClient",
    "IndexerInterface",
    "IndexerStubClient",
]
