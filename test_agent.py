from crewai import Agent, Task, Crew

agent = Agent(
    role="Analista",
    goal="Resumir texto",
    backstory="Experto en análisis",
    llm="ollama/llama3"
)

task = Task(
    description="Resume este texto: La empresa ha crecido mucho este año y ha duplicado sus ingresos...",
    expected_output="Un resumen claro en 2-3 líneas",  # 🔥 OBLIGATORIO
    agent=agent
)

crew = Crew(
    agents=[agent],
    tasks=[task]
)

print(crew.kickoff())