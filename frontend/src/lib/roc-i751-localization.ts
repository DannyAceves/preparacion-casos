import { QuestionnaireQuestion, QuestionnaireQuestionOption } from "@/types/workspace";

const ROC_DOCUMENT_LABELS: Record<string, string> = {
  conditional_resident_card: "Tarjeta de residente condicional (frente y reverso)",
  conditional_resident_photos: "Dos fotos tipo pasaporte del residente condicional",
  roc_questionnaire: "Cuestionario ROC completado",
  spouse_status_evidence: "Prueba del estatus del esposo/a ciudadano o residente",
  marriage_certificate: "Acta de matrimonio",
  joint_tax_returns: "Declaraciones conjuntas de impuestos federales",
  spouse_income_evidence: "W-2 o 1099 del esposo/a ciudadano o residente",
  recent_pay_stubs: "Talones de pago recientes",
  joint_bank_statements: "Estados de cuenta bancarios conjuntos",
  joint_credit_card_statements: "Estados de cuenta de tarjetas conjuntas",
  joint_housing_evidence: 'Contrato de renta o hipoteca con ambos nombres',
  joint_household_bills: "Recibos de servicios a nombre de ambos",
  joint_vehicle_evidence: "Evidencia de vehiculo o seguro conjunto",
  children_birth_certificates: "Actas de nacimiento de hijos en comun",
  pregnancy_evidence: "Evidencia de embarazo",
  relationship_photos: "Fotos familiares o de la relacion con descripcion",
  social_media_evidence: "Evidencia de redes sociales de la relacion",
  relationship_affidavits: "Declaraciones juradas de amigos o familiares",
  shared_financial_obligations: "Prueba de deudas o apoyo financiero compartido",
  prior_divorce_decree: "Sentencia de divorcio de un matrimonio anterior",
  prior_spouse_death_certificate: "Acta de defuncion de esposo/a anterior",
  criminal_disposition_records: "Resoluciones o cierres de antecedentes penales",
  child_dependent_identity_documents: "Tarjeta de residente y acta del hijo dependiente",
  child_dependent_photos: "Dos fotos tipo pasaporte por cada hijo dependiente",
};

const ROC_SECTION_LABELS: Record<string, { title: string; description?: string }> = {
  "Part 1. Conditional Resident Information": {
    title: "Parte 1. Informacion del residente condicional",
    description: "Datos de identidad, estado civil, direcciones e historial migratorio principal.",
  },
  "Part 2. Biographic Information": {
    title: "Parte 2. Informacion biografica",
    description: "Datos fisicos y biograficos requeridos para preparar la forma de USCIS.",
  },
  "Part 3. Basis for Petition": {
    title: "Parte 3. Base de la peticion",
    description: "Indica si la presentacion es conjunta o si aplica una exencion.",
  },
  "Part 4. U.S. Citizen or Resident Spouse Information": {
    title: "Parte 4. Informacion del esposo/a ciudadano o residente",
    description: "Datos de identidad y domicilio del familiar calificado.",
  },
  "Part 5. Children": {
    title: "Parte 5. Hijos",
    description: "Incluye a todos los hijos del residente condicional, sin importar la edad.",
  },
  "Part 6. Accommodations": {
    title: "Parte 6. Ajustes o apoyos requeridos",
    description: "Indica si alguien necesita apoyos por discapacidad o limitaciones.",
  },
  "Part 7. Language and Review": {
    title: "Parte 7. Idioma y revision final",
    description: "Detalles de idioma, comprension y comentarios para revision legal.",
  },
};

const ROC_QUESTION_LABELS: Record<
  string,
  {
    prompt: string;
    helpText?: string;
  }
> = {
  last_name: { prompt: "Apellido(s)" },
  first_name: { prompt: "Nombre(s)" },
  middle_name: { prompt: "Segundo nombre" },
  other_names_used: { prompt: "Otros nombres usados, incluyendo apodos, alias o apellido de soltera" },
  date_of_birth: { prompt: "Fecha de nacimiento" },
  country_of_birth: { prompt: "Pais de nacimiento" },
  country_of_citizenship: { prompt: "Pais de ciudadania o nacionalidad" },
  alien_registration_number: { prompt: "Numero de registro de extranjero (A-Number)" },
  ssn: { prompt: "Numero de Seguro Social de EE. UU." },
  uscis_elis_account_number: { prompt: "Numero de cuenta USCIS ELIS" },
  marital_status: { prompt: "Estado civil actual" },
  marriage_date: { prompt: "Fecha de matrimonio" },
  marriage_place: { prompt: "Lugar del matrimonio" },
  marriage_end_date: { prompt: "Si el matrimonio termino, indica la fecha de divorcio o fallecimiento" },
  conditional_residence_expires_on: { prompt: "Fecha de vencimiento de la residencia condicional" },
  mailing_address: {
    prompt: "Direccion postal",
    helpText: "Incluye calle, numero interior, ciudad, estado, codigo postal y cualquier linea adicional aplicable.",
  },
  physical_address_same_as_mailing: { prompt: "Tu direccion fisica es la misma que tu direccion postal?" },
  physical_address: { prompt: "Direccion fisica, si es distinta a la direccion postal" },
  in_removal_proceedings: { prompt: "Estas en proceso de remocion, deportacion o rescicion?" },
  third_party_fee_paid: { prompt: "Se le pago a alguien distinto de un abogado por ayuda con esta peticion?" },
  arrest_history: {
    prompt: "Alguna vez te han arrestado, detenido, acusado, multado, encarcelado o has cometido un delito en EE. UU. o en otro pais?",
  },
  arrest_history_explanation: { prompt: "Si respondiste que si, explica con detalle el historial penal o de arrestos" },
  different_marriage_basis: {
    prompt: "Si estas casado/a, es un matrimonio distinto al que te dio la residencia condicional?",
  },
  prior_addresses_since_residence: { prompt: "Lista todas las direcciones donde has vivido desde que eres residente permanente" },
  government_overseas_service: {
    prompt: "Tu esposo/a o el esposo/a de tu padre o madre trabaja actualmente para el Gobierno de EE. UU. fuera del pais?",
  },
  ethnicity: { prompt: "Etnicidad" },
  race: {
    prompt: "Raza o razas",
    helpText: "Si aplica mas de una, puedes escribirlas separadas por comas.",
  },
  height_feet: { prompt: "Estatura (pies)" },
  height_inches: { prompt: "Estatura (pulgadas)" },
  weight_lbs: { prompt: "Peso (libras)" },
  eye_color: { prompt: "Color de ojos" },
  hair_color: { prompt: "Color de cabello" },
  joint_filing_party: { prompt: "Si presentas conjuntamente, con quien presentas?" },
  waiver_basis: {
    prompt: "Si no puedes presentar conjuntamente, explica la base de la exencion",
    helpText: "Ejemplos: fallecimiento del esposo/a, divorcio, maltrato o crueldad extrema, o dificultad extrema.",
  },
  spouse_relationship: { prompt: "Relacion con el familiar calificado" },
  spouse_last_name: { prompt: "Apellido del esposo/a" },
  spouse_first_name: { prompt: "Nombre del esposo/a" },
  spouse_middle_name: { prompt: "Segundo nombre del esposo/a" },
  spouse_date_of_birth: { prompt: "Fecha de nacimiento del esposo/a" },
  spouse_ssn: { prompt: "Numero de Seguro Social del esposo/a" },
  spouse_a_number: { prompt: "A-Number del esposo/a" },
  spouse_physical_address: { prompt: "Direccion fisica del esposo/a" },
  children: { prompt: "Lista todos los hijos" },
  accommodation_requested_self: { prompt: "Solicitas algun apoyo o ajuste por discapacidad o limitacion?" },
  accommodation_requested_spouse: { prompt: "Tu esposo/a solicita algun apoyo o ajuste por discapacidad o limitacion?" },
  accommodation_requested_children: { prompt: "Algun hijo incluido solicita apoyos o ajustes por discapacidad o limitacion?" },
  accommodation_details: { prompt: "Describe los apoyos o ajustes solicitados" },
  petitioner_can_read_english: { prompt: "La persona que presenta la peticion puede leer y entender ingles?" },
  beneficiary_can_read_english: { prompt: "El beneficiario puede leer y entender ingles?" },
  additional_information: { prompt: "Informacion adicional o aclaraciones para la revision legal" },
};

const ROC_REPEATABLE_LABELS: Record<string, string> = {
  from: "Desde",
  to: "Hasta",
  street: "Calle",
  unit: "Numero interior",
  city: "Ciudad",
  county: "Condado",
  state: "Estado",
  zip: "Codigo postal",
  full_name: "Nombre completo",
  a_number: "A-Number",
  living_with_you: "Vive contigo?",
  applying_with_you: "Presenta contigo?",
  address: "Direccion",
  date_of_birth: "Fecha de nacimiento",
};

const OPTION_LABELS: Record<string, string> = {
  yes: "Si",
  no: "No",
  single: "Soltero/a",
  married: "Casado/a",
  divorced: "Divorciado/a",
  widowed: "Viudo/a",
  spouse: "Mi esposo/a",
  parents_spouse: "El esposo/a de mi padre o madre",
  hispanic_or_latino: "Hispano o latino",
  not_hispanic_or_latino: "No hispano o latino",
  black: "Negro",
  blue: "Azul",
  brown: "Cafe",
  gray: "Gris",
  green: "Verde",
  hazel: "Avellana",
  maroon: "Granate",
  pink: "Rosado",
  unknown_other: "Desconocido u otro",
  bald: "Calvo",
  blond: "Rubio",
  red: "Rojo",
  sandy: "Arena",
  white: "Blanco",
};

const OPTION_LABELS_BY_TEXT: Record<string, string> = {
  Yes: "Si",
  No: "No",
  Single: "Soltero/a",
  Married: "Casado/a",
  Divorced: "Divorciado/a",
  Widowed: "Viudo/a",
  "My spouse": "Mi esposo/a",
  "My parent's spouse": "El esposo/a de mi padre o madre",
  "Spouse or former spouse": "Esposo/a o exesposo/a",
  "Parent's spouse or former spouse": "Esposo/a o exesposo/a del padre o madre",
  "Hispanic or Latino": "Hispano o latino",
  "Not Hispanic or Latino": "No hispano o latino",
  Black: "Negro",
  Blue: "Azul",
  Brown: "Cafe",
  Gray: "Gris",
  Green: "Verde",
  Hazel: "Avellana",
  Maroon: "Granate",
  Pink: "Rosado",
  "Unknown or Other": "Desconocido u otro",
  Bald: "Calvo",
  Blond: "Rubio",
  Red: "Rojo",
  Sandy: "Arena",
  White: "Blanco",
};

export function isRocI751CaseType(caseType: string | null | undefined): boolean {
  return (caseType ?? "").trim().toLowerCase() === "roc-i751";
}

export function localizeRocSection(title: string, description: string | null | undefined): { title: string; description: string | null } {
  const localized = ROC_SECTION_LABELS[title];
  if (!localized) {
    return { title, description: description ?? null };
  }
  return {
    title: localized.title,
    description: localized.description ?? description ?? null,
  };
}

export function localizeRocQuestion(question: QuestionnaireQuestion): QuestionnaireQuestion {
  const localized = ROC_QUESTION_LABELS[question.key];
  return {
    ...question,
    prompt: localized?.prompt ?? question.prompt,
    help_text: localized?.helpText ?? question.help_text,
    options: localizeRocOptions(question.options),
  };
}

export function localizeRocOptions(options: QuestionnaireQuestionOption[] | null): QuestionnaireQuestionOption[] | null {
  if (!options) {
    return null;
  }
  return options.map((option) => ({
    ...option,
    label: OPTION_LABELS[option.value] ?? OPTION_LABELS_BY_TEXT[option.label] ?? option.label,
  }));
}

export function localizeRocDocumentLabel(documentType: string | null | undefined, fallback: string): string {
  if (!documentType) {
    return fallback;
  }
  return ROC_DOCUMENT_LABELS[documentType] ?? fallback;
}

export function localizeRocDocumentType(documentType: string | null | undefined): string {
  if (!documentType) {
    return "Documento de apoyo";
  }
  return ROC_DOCUMENT_LABELS[documentType] ?? documentType.replaceAll("_", " ");
}

export function localizeRocRepeatableField(fieldName: string): string {
  return ROC_REPEATABLE_LABELS[fieldName] ?? fieldName.replaceAll("_", " ");
}

export function localizeDocumentStatus(status: string): string {
  const labels: Record<string, string> = {
    received_from_client: "Recibido del cliente",
    processed: "Procesado",
    approved: "Aprobado",
    rejected: "Rechazado",
    archived: "Archivado",
    uploaded: "Cargado",
  };
  return labels[status] ?? status.replaceAll("_", " ");
}

export function localizeProcessingStatus(status: string): string {
  const labels: Record<string, string> = {
    queued: "En cola",
    processing: "Procesando",
    processed: "Procesado",
    failed: "Con error",
  };
  return labels[status] ?? status.replaceAll("_", " ");
}
