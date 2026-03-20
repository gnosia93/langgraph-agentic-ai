* 설정
```
# 설치
pip install langfuse

# .env 파일
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# 코드
from dotenv import load_dotenv
load_dotenv()

langfuse_handler = CallbackHandler()  # 자동으로 환경변수 읽음
```

* 호출 추적
```
방법 1: 콜백 직접 전달 (수동)
llm.invoke(input, config={"callbacks": [langfuse_handler]})

방법 2: 데코레이터 사용 (자동, 추천!)
@observe()
def my_function():
    llm.invoke(input)  # 자동으로 추적됨
데코레이터 방식이 훨씬 편해요. 어떤 방식으로 하실 건가요?
```


