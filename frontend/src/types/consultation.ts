import { Case } from "@/types/case";
import { Client } from "@/types/client";

export interface Consultation {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  date_of_birth: string | null;
  appointment_at: string | null;
  assigned_attorney: string | null;
  reception_notes: string | null;
  intake_answers: string | null;
  suggested_case_type: string | null;
  status: string;
  client_id: string | null;
  converted_case_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateConsultationInput {
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  date_of_birth?: string | null;
  appointment_at?: string | null;
  assigned_attorney?: string | null;
  reception_notes?: string | null;
  intake_answers?: string | null;
  suggested_case_type?: string | null;
  status?: string;
}

export interface UpdateConsultationInput extends Partial<CreateConsultationInput> {}

export interface ConvertConsultationInput {
  case_number: string;
  case_type?: string | null;
  title: string;
  summary?: string | null;
}

export interface ConsultationConversionResult {
  consultation: Consultation;
  client: Client;
  case: Case;
}
