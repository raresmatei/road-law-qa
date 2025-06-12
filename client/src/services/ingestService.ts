// src/services/ingestService.ts
import apiClient from './api';

//
// 1) TS interfaces for the request + response
export interface IngestRequest {
  url: string;
}

export interface IngestResponse {
  inserted_chunks: number;
}

//
// 2) call the admin ingest endpoint
export async function ingestLegislation(
  payload: IngestRequest
): Promise<IngestResponse> {
  const response = await apiClient.post<IngestResponse>(
    '/admin/ingest_legislation',
    payload
  );
  return response.data;
}
