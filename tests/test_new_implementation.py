import pytest
from unittest.mock import Mock, patch
from app.services.interfaces import (
    AIServiceInterface,
    DatabaseServiceInterface,
    CacheServiceInterface,
    LoggingServiceInterface
)
from app.services.container import get_container
from app.chatbot.factory import get_registry, create_chatbot
from app.chatbot.base_new import BaseChatbot
from app.chatbot.vendas_new import VendasChatbot
from app.chatbot.treinamento_new import TreinamentoChatbot
from app.chatbot.whatsapp_new import WhatsAppChatbot

@pytest.fixture
def mock_services():
    """Fixture to provide mock services."""
    return {
        "ai_service": Mock(spec=AIServiceInterface),
        "db_service": Mock(spec=DatabaseServiceInterface),
        "cache_service": Mock(spec=CacheServiceInterface),
        "logger": Mock(spec=LoggingServiceInterface)
    }

@pytest.fixture
def container(mock_services):
    """Fixture to provide a configured service container."""
    container = get_container()
    for interface, service in mock_services.items():
        container.register(type(service), service)
    return container

def test_chatbot_creation(container):
    """Test creation of different chatbot types."""
    registry = get_registry()
    
    # Test vendas chatbot
    vendas_bot = registry.create_chatbot("vendas")
    assert isinstance(vendas_bot, VendasChatbot)
    
    # Test treinamento chatbot
    treinamento_bot = registry.create_chatbot("treinamento")
    assert isinstance(treinamento_bot, TreinamentoChatbot)
    
    # Test whatsapp chatbot
    whatsapp_bot = registry.create_chatbot("whatsapp")
    assert isinstance(whatsapp_bot, WhatsAppChatbot)

def test_chatbot_service_injection(mock_services):
    """Test that services are properly injected into chatbots."""
    vendas_bot = VendasChatbot(**mock_services)
    
    assert vendas_bot._ai_service == mock_services["ai_service"]
    assert vendas_bot._db_service == mock_services["db_service"]
    assert vendas_bot._cache_service == mock_services["cache_service"]
    assert vendas_bot._logger == mock_services["logger"]

def test_chatbot_message_processing(mock_services):
    """Test message processing with mocked services."""
    # Configure mock responses
    mock_services["ai_service"].send_message.return_value = {
        "content": "Test response",
        "id": "msg_123"
    }
    
    # Create chatbot instance
    vendas_bot = VendasChatbot(**mock_services)
    
    # Process a message
    response = vendas_bot.process_message(
        thread_id="thread_123",
        message="Test message",
        user_name="Test User"
    )
    
    # Verify service interactions
    mock_services["ai_service"].send_message.assert_called_once()
    mock_services["db_service"].log_interaction.assert_called()
    assert "response" in response
    assert "thread_id" in response

def test_chatbot_caching(mock_services):
    """Test caching behavior."""
    # Configure mock cache
    mock_services["cache_service"].get.return_value = None
    mock_services["cache_service"].set.return_value = True
    
    # Create chatbot instance
    whatsapp_bot = WhatsAppChatbot(**mock_services)
    
    # Test cache usage
    result = whatsapp_bot.analyze_conversation(
        chat_id="chat_123",
        metrics=["response_time", "sentiment"]
    )
    
    # Verify cache interactions
    mock_services["cache_service"].get.assert_called_once()
    mock_services["cache_service"].set.assert_called_once()

def test_error_handling(mock_services):
    """Test error handling in chatbots."""
    # Configure mock to raise an exception
    mock_services["ai_service"].send_message.side_effect = Exception("Test error")
    
    # Create chatbot instance
    treinamento_bot = TreinamentoChatbot(**mock_services)
    
    # Test error handling
    response = treinamento_bot.process_message(
        thread_id="thread_123",
        message="Test message"
    )
    
    # Verify error logging and response
    mock_services["logger"].error.assert_called()
    assert "error" in response

def test_chatbot_registry():
    """Test chatbot registry functionality."""
    registry = get_registry()
    
    # Test listing chatbots
    chatbots = registry.list_chatbots()
    assert "vendas" in chatbots
    assert "treinamento" in chatbots
    assert "whatsapp" in chatbots
    
    # Test invalid chatbot type
    with pytest.raises(ValueError):
        registry.create_chatbot("invalid_type")

def test_convenience_functions():
    """Test convenience functions for chatbot creation."""
    # Test create_chatbot function
    vendas_bot = create_chatbot("vendas")
    assert isinstance(vendas_bot, VendasChatbot)
    
    # Test list_available_chatbots function
    from app.chatbot import list_chatbots
    available_bots = list_chatbots()
    assert isinstance(available_bots, dict)
    assert len(available_bots) > 0

@pytest.mark.asyncio
async def test_async_operations(mock_services):
    """Test asynchronous operations."""
    # Configure mock for async operation
    mock_services["ai_service"].create_thread.return_value = "thread_123"
    
    # Create chatbot instance
    whatsapp_bot = WhatsAppChatbot(**mock_services)
    
    # Test async operation
    thread_id = whatsapp_bot.create_thread()
    assert thread_id == "thread_123"

def test_service_container_singleton():
    """Test that service container maintains singleton instances."""
    container1 = get_container()
    container2 = get_container()
    
    assert container1 is container2
    
    # Test service registration
    mock_service = Mock(spec=AIServiceInterface)
    container1.register(AIServiceInterface, mock_service)
    
    assert container2.get(AIServiceInterface) is mock_service

def test_chatbot_cleanup():
    """Test cleanup of chatbot resources."""
    from app.chatbot import get_chatbot, cleanup_chatbots
    
    # Create some chatbots
    vendas_bot = get_chatbot("vendas")
    treinamento_bot = get_chatbot("treinamento")
    
    # Perform cleanup
    cleanup_chatbots()
    
    # Verify cleanup was successful
    from app.chatbot import get_active_chatbots
    active_bots = get_active_chatbots()
    assert len(active_bots) == 0
