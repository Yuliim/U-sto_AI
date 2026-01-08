# 4. 답변 안정성 테스트
# 개념: LLM의 답변이 일관성 있고 신뢰할 수 있는지 검증. 
# 테스트 케이스를 작성하고, 답변의 정확성과 규칙 준수 여부를 확인.

# fallback 안정성
# 출력 포맷 일관성
# 출처 필수 포함

# unit_tests.py

import unittest
from app.config import RETRIEVER_TOP_K, NO_CONTEXT_RESPONSE, llm, vectordb
from rag.chain import run_rag_chain

class TestRAGChain(unittest.TestCase):

    def test_no_context_response(self):
        response = run_rag_chain(llm, vectordb, "존재하지 않는 질문")
        self.assertEqual(response["answer"], NO_CONTEXT_RESPONSE)

    def test_answer_format(self):
        response = run_rag_chain(llm, vectordb, "질문")
        self.assertTrue(response["answer"].endswith("하십시오."))

    def test_attribution_exists(self):
        response = run_rag_chain(llm, vectordb, "질문")
        self.assertTrue(len(response["attribution"]) > 0)

    def test_attribution_fields(self):
        response = run_rag_chain(llm, vectordb, "질문")
        first = response["attribution"][0]
        self.assertIn("doc_id", first)
        self.assertIn("score", first)

if __name__ == "__main__":
    unittest.main()
