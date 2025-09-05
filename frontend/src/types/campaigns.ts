export interface Campaign {
  campaign_id: string;
  name: string;
  list_id: string;
  subject_line: string;
  google_doc_url: string;
  created_at: string;
  created_by: string;
  sent_at: string | null;
  status: 'draft' | 'sending' | 'sent' | 'failed';
  sendgrid_batch_id: string | null;
  stats: CampaignStats;
}

export interface CampaignStats {
  total_recipients: number;
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  bounced: number;
  unsubscribed?: number;
  last_updated: string;
  delivery_rate?: number;
  open_rate?: number;
  click_rate?: number;
  bounce_rate?: number;
}

export interface CampaignEvent {
  event_id: string;
  master_id: string;
  timestamp: string;
  event_type: string;
  email_data?: {
    campaign_id: string;
    email_address: string;
    subject_line?: string;
    sendgrid_event_id?: string;
    sendgrid_message_id?: string;
    bounce_reason?: string;
  };
  interaction_data?: {
    ip_address?: string;
    user_agent?: string;
    clicked_url?: string;
  };
}

export interface CreateCampaignRequest {
  name: string;
  list_id: string;
  subject_line: string;
  google_doc_url: string;
}

export interface TestEmailRequest {
  test_email: string;
}