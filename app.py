import streamlit as st
import pandas as pd
from src.pdf_processor import extract_text_from_pdf
from src.ai_analyst import analyze_candidate

# Configuração da Página
st.set_page_config(page_title="Recruiting Assistant", page_icon="🔍", layout="wide")

# --- FUNÇÃO AUXILIAR DE UI ---
def render_custom_input(label, options, key_prefix):
    """
    Renderiza um selectbox que, se escolhido 'Outro', mostra um text_input.
    Retorna o valor final escolhido/digitado.
    """
    selected = st.selectbox(label, options + ["Outro (Digitar manualmente)"], key=f"sel_{key_prefix}")
    
    if "Outro" in selected:
        custom_val = st.text_input(f"Digite {label}:", key=f"txt_{key_prefix}")
        return custom_val if custom_val else None # Retorna None se estiver vazio
    return selected

def main():
    st.title("🔍 ATS Inteligente: Análise de Currículos")
    
    with st.sidebar:
        st.header("🔑 Acesso")
        api_key = st.text_input("Gemini API Key", type="password")
        #st.info("Soft Skills agora são critérios de match explícitos.")

    # --- 1. DEFINIÇÃO DA VAGA (JOB SPEC) ---
    st.subheader("1. Definição da Vaga")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        areas_list = ["Engenharia de Software", "Dados & IA", "Infraestrutura/Cloud", "Produto/Design", "Comercial/Vendas"]
        area = render_custom_input("Área", areas_list, "area")
    
    with c2:
        # Lista genérica, pois agora temos o campo "Outro"
        cargos_list = ["Backend Developer", "Frontend Developer", "Data Scientist", "Product Manager", "DevOps Engineer"]
        cargo = render_custom_input("Cargo", cargos_list, "cargo")
        
    with c3:
        seniority_list = ["Estagiário", "Júnior", "Pleno", "Sênior", "Tech Lead", "Principal/Staff"]
        senioridade = render_custom_input("Senioridade", seniority_list, "senioridade")

    st.divider()
    
    # --- 2. REQUISITOS TÉCNICOS E COMPORTAMENTAIS ---
    col_tech, col_soft = st.columns(2)
    
    with col_tech:
        st.markdown("#### 🛠️ Hard Skills (Técnicas)")
        tech_options = ["Python", "Java", "JavaScript", "React", "SQL", "AWS", "Docker", "Kubernetes", "Git", "Excel Avançado"]
        selected_tech = st.multiselect("Selecione da lista:", tech_options)
        extra_tech = st.text_input("Outras tecnologias (separadas por vírgula):", placeholder="Ex: Rust, Terraform, PowerBI")
        
        # Combina a lista com o texto livre
        final_tech_stack = selected_tech
        if extra_tech:
            final_tech_stack += [t.strip() for t in extra_tech.split(",") if t.strip()]

    with col_soft:
        st.markdown("#### 🧠 Soft Skills (Comportamentais)")
        # Lista baseada nas skills mais pedidas do LinkedIn
        soft_options = [
            "Comunicação Clara", "Trabalho em Equipe", "Liderança", "Resolução de Problemas", 
            "Inteligência Emocional", "Adaptabilidade", "Pensamento Crítico", "Autogestão"
        ]
        selected_soft = st.multiselect("O que é essencial para a vaga?", soft_options)
        extra_soft = st.text_input("Outras comportamentais:", placeholder="Ex: Negociação, Foco no Cliente")
        
        final_soft_stack = selected_soft
        if extra_soft:
            final_soft_stack += [s.strip() for s in extra_soft.split(",") if s.strip()]

    # Descrição livre para nuances
    descricao_extra = st.text_area("Contexto Adicional (Cultura, Projetos, Benefícios):", height=80)

    # --- MONTAGEM DO CONTEXTO ---
    job_context = {
        "cargo": cargo,
        "senioridade": senioridade,
        "area": area,
        "tech_stack_obrigatoria": final_tech_stack,
        "soft_skills_desejadas": final_soft_stack,
        "detalhes_extras": descricao_extra
    }

    # --- 3. UPLOAD E ANÁLISE ---
    st.divider()
    uploaded_files = st.file_uploader("Upload de Currículos (PDF)", type=["pdf"], accept_multiple_files=True)

    if st.button("🔍 Analisar Compatibilidade", type="primary"):
        if not api_key:
            st.error("Falta a API Key.")
            return
            
        # Validação simples para garantir que o usuário preencheu o mínimo
        if not cargo or not area:
            st.warning("Por favor, defina pelo menos a Área e o Cargo (use 'Outro' se necessário).")
            return

        results = []
        prog_bar = st.progress(0)
        
        for i, pdf in enumerate(uploaded_files):
            text = extract_text_from_pdf(pdf)
            if text:
                # Passamos o dicionário job_context direto agora
                analise = analyze_candidate(api_key, text, job_context)
                if analise.get("candidato_nome") == "Nome Completo": 
                    analise["candidato_nome"] = pdf.name
                results.append(analise)
            prog_bar.progress((i + 1) / len(uploaded_files))
            
        if results:
            df = pd.DataFrame(results).sort_values("score", ascending=False)
            
            st.subheader("🏆 Ranking Final")
            
            # Tabela Resumida
            st.dataframe(
                df[["candidato_nome", "score", "hard_skills_identificadas", "soft_skills_identificadas"]],
                column_config={
                    "score": st.column_config.ProgressColumn("Match", format="%d", min_value=0, max_value=100),
                    "hard_skills_identificadas": "Tech Stack",
                    "soft_skills_identificadas": "Soft Skills"
                },
                use_container_width=True, hide_index=True
            )
            
            st.markdown("---")
            st.subheader("📝 Detalhamento da IA")

            for _, row in df.iterrows():
                # Título do Expander com Score e Nome
                with st.expander(f"{row['score']}% - {row['candidato_nome']}"):
                    
                    # 1. Justificativa em Azul (Info)
                    st.info(f"🤖 **Parecer da IA:** {row['justificativa_resumida']}")
                    
                    # 2. Colunas coloridas para Pontos Fortes e Fracos
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        # Caixa Verde para Pontos Fortes
                        st.success(" **Pontos Fortes & Match**")
                        if row.get('pontos_fortes'):
                            for ponto in row['pontos_fortes']:
                                st.markdown(f"- {ponto}")
                        else:
                            st.write("Nenhum destaque específico identificado.")
                            
                    with c2:
                        # Caixa Vermelha/Laranja para Pontos Fracos/Gaps
                        st.error(" **Gaps & Pontos de Atenção**")
                        if row.get('pontos_fracos'):
                            for ponto in row['pontos_fracos']:
                                st.markdown(f"- {ponto}")
                        else:
                            st.write("Nenhum gap crítico identificado.")

                    # Exibição das Skills encontradas (Opcional, mas visualmente agradável)
                    st.caption(f"**Tech Skills Validadas:** {', '.join(row.get('hard_skills_identificadas', []))}")
if __name__ == "__main__":
    main()
