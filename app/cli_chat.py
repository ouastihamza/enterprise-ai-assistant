from app.services.rag_service import RAGService


def main():
    rag_service = RAGService(
        chunks_path="storage/processed/cv_chunks.json"
    )

    print("=" * 50)
    print("        AI Document Assistant - RAG v1")
    print("=" * 50)
    print("Ask questions about the uploaded document.")
    print("Type 'exit' to quit.\n")

    while True:
        user_question = input("You: ")

        if user_question.lower() == "exit":
            print("\nGoodbye!")
            break

        answer = rag_service.answer_question(user_question)

        print("\nAssistant:")
        print(answer)
        print()


if __name__ == "__main__":
    main()

#main.py==> takes user input => builds prompt =>calls llm_client.py =>prints answer
#before it was just user asking a question and it ends, now with this code its multiple questions till the user says exit. its becoming more like an app 
#the application now remembers what im saying to it