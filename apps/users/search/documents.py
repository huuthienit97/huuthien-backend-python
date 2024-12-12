from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analyzer
from .config import UserSearchConfig
from apps.users.models import User

# Tạo analyzer cho tiếng Việt
vietnamese_analyzer = analyzer(
    'vietnamese_analyzer',
    tokenizer='standard',
    filter=['lowercase', 'asciifolding']
)

@registry.register_document
class UserDocument(Document):
    username = fields.TextField(
        analyzer=vietnamese_analyzer,
        fields={'raw': fields.KeywordField()}
    )
    email = fields.TextField(
        analyzer=vietnamese_analyzer,
        fields={'raw': fields.KeywordField()}
    )
    full_name = fields.TextField(
        analyzer=vietnamese_analyzer
    )
    suggest = fields.CompletionField()
    is_active = fields.BooleanField()
    date_joined = fields.DateField()
    
    class Index:
        name = UserSearchConfig.INDEX_NAME
        settings = UserSearchConfig.get_index_settings()
    
    class Django:
        model = User
        fields = [
            'id'
        ]
    
    def prepare_suggest(self, instance):
        """Chuẩn bị data cho suggest"""
        suggestions = []
        for field in UserSearchConfig.SUGGEST_FIELDS:
            value = getattr(instance, field, None)
            if value:
                suggestions.append(value)
        return suggestions
        
    def prepare_full_name(self, instance):
        """Chuẩn bị full_name từ first_name và last_name"""
        return f"{instance.first_name} {instance.last_name}".strip()