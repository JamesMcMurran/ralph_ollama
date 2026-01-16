-- Add priority field to tasks table
ALTER TABLE tasks ADD COLUMN priority ENUM('high', 'medium', 'low') DEFAULT 'medium';