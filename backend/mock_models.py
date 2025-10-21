"""
Mock database models for local testing
"""

class MockMemoRequest:
    def __init__(self, **kwargs):
        self.id = 1  # Always return ID 1 for testing
        self.user_id = kwargs.get('user_id', 1)
        self.company_name = kwargs.get('company_name', 'Test Company')
        self.sources_id = kwargs.get('sources_id', 1)
        self.memo_type = kwargs.get('memo_type', 'full')
        self.status = kwargs.get('status', 'in_progress')
        self.error_log = None

class MockSession:
    def __init__(self):
        self.memo_requests = []
        self.next_id = 1
    
    def add(self, obj):
        if hasattr(obj, '__class__') and 'MemoRequest' in str(obj.__class__):
            obj.id = self.next_id
            self.next_id += 1
            self.memo_requests.append(obj)
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass
    
    def close(self):
        pass
    
    def query(self, model):
        return MockQuery(self.memo_requests)

class MockQuery:
    def __init__(self, data):
        self.data = data
    
    def filter(self, *args):
        return self
    
    def first(self):
        return self.data[0] if self.data else None
    
    def all(self):
        return self.data
