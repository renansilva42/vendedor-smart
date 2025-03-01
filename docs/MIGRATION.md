# Migration Guide: Chatbot Architecture Refactoring

This document outlines the steps to migrate from the old chatbot architecture to the new service-based architecture.

## Overview of Changes

### Key Improvements
- Separation of concerns through service interfaces
- Dependency injection for better testability
- Centralized logging and error handling
- Improved caching strategy
- Better type hints and documentation
- Factory pattern for chatbot creation
- Consistent error handling across components

### New Architecture Components

1. Service Layer:
   - `AIServiceInterface` - OpenAI API interactions
   - `DatabaseServiceInterface` - Database operations
   - `CacheServiceInterface` - Caching operations
   - `LoggingServiceInterface` - Centralized logging

2. Chatbot Components:
   - `BaseChatbot` - Enhanced base class with service integration
   - Specialized chatbots (Vendas, Treinamento, WhatsApp)
   - `ChatbotRegistry` - Factory for chatbot creation

3. Service Container:
   - Dependency injection container
   - Service lifecycle management
   - Configuration management

## Migration Steps

### 1. Service Layer Migration

```python
# Old way
from openai import OpenAI
client = OpenAI(api_key=Config.OPENAI_API_KEY)

# New way
from app.services.container import get_container
from app.services.interfaces import AIServiceInterface

ai_service = get_container().get(AIServiceInterface)
```

### 2. Chatbot Creation

```python
# Old way
from app.chatbot import VendasChatbot
chatbot = VendasChatbot()

# New way
from app.chatbot import get_chatbot
chatbot = get_chatbot("vendas")
```

### 3. Database Operations

```python
# Old way
from supabase import create_client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# New way
from app.services.container import get_container
from app.services.interfaces import DatabaseServiceInterface

db_service = get_container().get(DatabaseServiceInterface)
```

### 4. Caching Implementation

```python
# Old way
@lru_cache(maxsize=100)
def some_cached_function():
    pass

# New way
from app.services.container import get_container
from app.services.interfaces import CacheServiceInterface

cache_service = get_container().get(CacheServiceInterface)
cache_service.get("key")
cache_service.set("key", value, ttl=3600)
```

### 5. Logging Updates

```python
# Old way
logger = logging.getLogger(__name__)

# New way
from app.services.container import get_container
from app.services.interfaces import LoggingServiceInterface

logger = get_container().get(LoggingServiceInterface)
```

## File Replacements

1. Replace existing files with their new versions:
   - `base.py` → `base_new.py`
   - `vendas.py` → `vendas_new.py`
   - `treinamento.py` → `treinamento_new.py`
   - `whatsapp.py` → `whatsapp_new.py`
   - `__init__.py` → `__init__new.py`

2. Update imports in dependent files:
   ```python
   # Update imports to use new modules
   from app.chatbot.base_new import BaseChatbot
   from app.chatbot.vendas_new import VendasChatbot
   ```

## Testing the Migration

1. Create test cases for new functionality:
   ```python
   def test_chatbot_creation():
       chatbot = get_chatbot("vendas")
       assert isinstance(chatbot, VendasChatbot)
       
   def test_service_injection():
       container = get_container()
       ai_service = container.get(AIServiceInterface)
       assert ai_service is not None
   ```

2. Run existing tests with new implementation:
   ```bash
   python -m pytest tests/
   ```

## Rollback Plan

If issues are encountered:

1. Keep old files as backup:
   ```bash
   mv app/chatbot/base.py app/chatbot/base.py.new
   mv app/chatbot/base.py.old app/chatbot/base.py
   ```

2. Revert service container initialization:
   ```python
   # Revert to direct client creation
   from openai import OpenAI
   client = OpenAI(api_key=Config.OPENAI_API_KEY)
   ```

## Gradual Migration Strategy

1. Phase 1: Infrastructure
   - Deploy new service interfaces
   - Set up dependency injection container
   - Implement new logging system

2. Phase 2: Core Components
   - Migrate base chatbot class
   - Update specialized chatbots
   - Implement factory pattern

3. Phase 3: Integration
   - Update API endpoints
   - Migrate existing instances
   - Update documentation

4. Phase 4: Cleanup
   - Remove old implementations
   - Update tests
   - Finalize documentation

## Post-Migration Tasks

1. Update Documentation:
   - API documentation
   - Service interfaces
   - Configuration guide
   - Testing guide

2. Monitor Performance:
   - Response times
   - Error rates
   - Resource usage

3. Validate Features:
   - Chatbot functionality
   - Integration points
   - Error handling

## Best Practices

1. Service Usage:
   ```python
   # Get services from container
   container = get_container()
   ai_service = container.get(AIServiceInterface)
   db_service = container.get(DatabaseServiceInterface)
   cache_service = container.get(CacheServiceInterface)
   logger = container.create_logger("component.name")
   ```

2. Error Handling:
   ```python
   try:
       result = ai_service.process_message(message)
   except Exception as e:
       logger.error(f"Error processing message: {str(e)}", exc_info=True)
       raise
   ```

3. Caching Strategy:
   ```python
   # Use structured cache keys
   cache_key = f"{entity_type}:{entity_id}:{action}"
   cached_value = cache_service.get(cache_key)
   ```

## Support and Maintenance

1. Monitoring:
   - Implement service health checks
   - Set up error tracking
   - Monitor performance metrics

2. Troubleshooting:
   - Check service logs
   - Verify configuration
   - Test service connections

3. Updates:
   - Regular dependency updates
   - Security patches
   - Performance optimizations

## Contact

For questions or support during migration:
- Technical Lead: [Contact Information]
- Documentation: [Wiki Link]
- Issue Tracking: [Issue Tracker Link]
