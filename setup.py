from setuptools import setup, find_packages

setup(
    name="collector",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "streamlit>=1.45.0",
        "langchain>=0.3.0",
        "langchain-core>=0.3.0",
        "langchain-community>=0.3.0",
        "langgraph>=0.4.0",
        "ollama>=0.4.0",
        "langsmith>=0.3.0",
        "langchain-openai>=0.3.0",
    ],
    python_requires=">=3.10",
) 