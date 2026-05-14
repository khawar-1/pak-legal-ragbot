import os
import sys

# Add the parent directory of 'api' to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.retrieval import retrieval

def test_retrieval(query):
    print(f"\nQuery: {query}")
    print("-" * 40)
    answer, context = retrieval(query)
    print(f"Answer:\n{answer}")

if __name__ == "__main__":
    # Test vague queries
    test_retrieval("Tell me about property law.")
    test_retrieval("I have a land dispute.")
    
    # Test concrete queries
    test_retrieval("What is pre-emption in Pakistani law?")
    test_retrieval("Explain case 2008 CLC 332")
