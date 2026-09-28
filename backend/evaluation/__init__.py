"""Vlerësimi i UniMate AI për kapitullin e rezultateve të diplomës.

Përgjigjet ndaj pyetjeve kërkimore të temës:

- Sa saktë e zgjedh Router-i agjentin e duhur?      -> run_agents
- A e përmirëson RAG saktësinë e përgjigjeve?         -> run_retrieval,
                                                         run_baseline
- Si krahasohet multi-agent me një chatbot të vetëm?  -> run_baseline
- Sa efektiv është sistemi në trajtimin e kërkesave?  -> run_agents
- Sa shpesh përgjigjet citojnë burimin?               -> run_agents

Rendi i ekzekutimit, brenda kontejnerit të API-t:

    python -m evaluation.run_retrieval            # falas, pa LLM
    python -m evaluation.run_agents --max-cost 1.2
    python -m evaluation.run_baseline --max-cost 0.2
    python -m evaluation.report

Rezultatet shkruhen te `evaluation/results/`.
"""
