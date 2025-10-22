-- Add memo_type column to memo_requests table
ALTER TABLE memo_requests ADD COLUMN memo_type VARCHAR(50) DEFAULT 'full';
