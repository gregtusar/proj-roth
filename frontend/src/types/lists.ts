export interface VoterList {
  id: string;
  name: string;
  description?: string;
  query: string;
  created_at: string;
  updated_at: string;
  row_count?: number;
  user_id: string;
}

export interface QueryResult {
  columns: string[];
  rows: any[][];
  total_rows: number;
  execution_time: number;
  query: string;
}

export interface ListsState {
  userLists: VoterList[];
  selectedList: VoterList | null;
  queryResults: QueryResult | null;
  isLoading: boolean;
  isModalOpen: boolean;
  error: string | null;
}