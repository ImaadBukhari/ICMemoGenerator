"""
Mock models for local testing
"""

class MockSource:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.company_name = kwargs.get('company_name', 'Test Company')
        self.affinity_data = kwargs.get('affinity_data', {})
        self.perplexity_data = kwargs.get('perplexity_data', {})
        self.gmail_data = kwargs.get('gmail_data', {})
        self.drive_data = kwargs.get('drive_data', {})

class MockMemoSection:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', 1)
        self.memo_request_id = kwargs.get('memo_request_id', 1)
        self.section_name = kwargs.get('section_name', 'test_section')
        self.content = kwargs.get('content', 'Test content')
        self.data_sources = kwargs.get('data_sources', [])
        self.status = kwargs.get('status', 'completed')
        self.error_log = kwargs.get('error_log', None)

class MockMemoRequest:
    def __init__(self, **kwargs):
        self.id = 1
        self.user_id = kwargs.get('user_id', 1)
        self.company_name = kwargs.get('company_name', 'Test Company')
        self.sources_id = kwargs.get('sources_id', 1)
        self.memo_type = kwargs.get('memo_type', 'full')
        self.status = kwargs.get('status', 'in_progress')
        self.error_log = None

class MockSession:
    def __init__(self):
        self.memo_requests = []
        self.memo_sections = []
        self.sources = [MockSource(id=1, company_name="Test Company")]
        self.next_id = 1
    
    def add(self, obj):
        if hasattr(obj, '__class__'):
            if 'MockMemoRequest' in str(obj.__class__):
                obj.id = self.next_id
                self.next_id += 1
                self.memo_requests.append(obj)
            elif 'MockMemoSection' in str(obj.__class__):
                obj.id = self.next_id
                self.next_id += 1
                self.memo_sections.append(obj)
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass
    
    def close(self):
        pass
    
    def query(self, model):
        if hasattr(model, '__name__'):
            if model.__name__ == 'Source':
                return MockQuery(self.sources)
            elif model.__name__ == 'MemoRequest':
                return MockQuery(self.memo_requests)
            elif model.__name__ == 'MemoSection':
                return MockQuery(self.memo_sections)
        return MockQuery([])

class MockQuery:
    def __init__(self, data=None):
        self.data = data or []
    
    def filter(self, *args):
        return self
    
    def first(self):
        return self.data[0] if self.data else None
    
    def all(self):
        return self.data
