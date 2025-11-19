import google.generativeai as genai
import json

def analyze_candidate(api_key, resume_text, job_context):
    """
    job_context agora é um DICIONÁRIO rico com tech_stack e soft_skills separadas.
    """
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.0, # Zero criatividade, máximo foco analítico
        "response_mime_type": "application/json"
    }

    model = genai.GenerativeModel('models/gemini-2.5-flash', generation_config=generation_config)

    # Transformamos o dict em string formatada para o prompt
    context_str = json.dumps(job_context, indent=2, ensure_ascii=False)

    prompt = f"""
    Você é um Headhunter Sênior e especialista em análise técnica.
    
    Sua missão é calcular o "Fit Score" (0-100) de um candidato baseado em requisitos EXPLÍCITOS.
    
    --- REQUISITOS DA VAGA (INPUT) ---
    {context_str}
    
    --- CANDIDATO (TEXTO EXTRAÍDO DO PDF) ---
    {resume_text}
    
    --- REGRAS DE ANÁLISE ---
    1. Hard Skills: Verifique se o candidato possui as tecnologias listadas em 'tech_stack_obrigatoria'.
    2. Soft Skills: Procure por EVIDÊNCIAS no texto que sugiram as skills pedidas em 'soft_skills_desejadas' (não apenas a palavra-chave, mas contextos como "liderou equipe", "apresentou resultados", etc).
    3. Senioridade: Compare o tempo de experiência e cargos anteriores com a 'senioridade' pedida.
    
    SAÍDA OBRIGATÓRIA (JSON):
    {{
        "candidato_nome": "Nome extraído",
        "score": 0,
        "hard_skills_identificadas": ["Lista das skills da vaga que o candidato TEM"],
        "soft_skills_identificadas": ["Lista das soft skills da vaga que o candidato DEMONSTRA"],
        "pontos_fortes": ["Breve lista"],
        "pontos_fracos": ["Breve lista (gaps em relação à vaga)"],
        "justificativa_resumida": "Explique o score em 1 frase focado no GAP ou no MATCH."
    }}
    """
    
    error_response = {
        "candidato_nome": "Erro Leitura",
        "score": 0,
        "hard_skills_identificadas": [],
        "soft_skills_identificadas": [],
        "pontos_fortes": [],
        "pontos_fracos": [],
        "justificativa_resumida": "Erro ao processar."
    }

    try:
        response = model.generate_content(prompt)
        text_clean = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(text_clean)
    except Exception as e:
        error_response["justificativa_resumida"] = f"Erro API: {str(e)}"
        return error_response