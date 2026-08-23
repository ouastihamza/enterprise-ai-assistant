export interface KnowledgeDocument {
  id: number;
  name: string;
  file_size: number;
  chunk_count: number;
  indexed: boolean;
  status: string;
  uploaded_at: string | null;
  last_indexed: string | null;
  error_message: string | null;
}