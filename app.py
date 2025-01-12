import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
import re
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()

# OpenAI API 키 설정
try:
    api_key = os.getenv('OPENAI_API_KEY')
except:
    api_key = st.secrets.get('OPENAI_API_KEY')
    
if not api_key:
    st.error('OpenAI API 키가 설정되지 않았습니다. secrets.toml 파일이나 환경변수에 OPENAI_API_KEY를 설정해주세요.')
    st.stop()

client = OpenAI(api_key=api_key)

def summarize_text(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text in Korean."},
                {"role": "user", "content": f"다음 텍스트를 한국어로 간단히 요약해주세요:\n\n{text}"}
                
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"요약 중 오류가 발생했습니다: {str(e)}")
        print(f"Error details: {e}")
        return None

def extract_video_id(youtube_url):
    # YouTube URL에서 video ID를 추출하는 함수
    video_id_pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(video_id_pattern, youtube_url)
    if match:
        return match.group(1)
    return None

def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko', 'en'])
        return transcript
    except Exception as e:
        return None

def format_summary_for_thread(summary):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "온라인 커뮤니티에서 사용하기 좋은 포맷으로 텍스트를 변환하는 assistant입니다."},
                {"role": "user", "content": f"""
                다음 텍스트를 온라인 커뮤니티 형식으로 변환해주세요:
                - 제목/요약을 맨 위에 굵게 표시
                - 중요 포인트는 번호를 매겨서 정리
                - 각 포인트는 간단명료하게
                - 마지막에 TLDR 추가
                
                텍스트: {summary}
                """}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"포맷 변환 중 오류가 발생했습니다: {str(e)}")
        return summary

# Streamlit 앱 제목
st.title('YouTube To Thread Converter')

# 입력 필드와 검색 버튼을 나란히 배치하기 위한 컬럼 생성
container = st.container()
col1, col2 = container.columns([4, 1])

with col1:
    # YouTube URL 입력 필드
    youtube_url = st.text_input('', placeholder='YouTube URL을 입력하세요', key='url_input', label_visibility='collapsed')

with col2:
    # 검색 버튼 (container를 사용하여 수직 정렬)
    search_button = st.button('검색', use_container_width=True)

# 검색 버튼을 클릭했을 때만 실행
if search_button and youtube_url:
    video_id = extract_video_id(youtube_url)
    
    if video_id:
        transcript = get_transcript(video_id)
        
        if transcript:
            # 영상 미리보기 표시
            st.video(youtube_url)
            
            # 자막 텍스트 표시
            st.subheader('자막 내용:')
            
            # 전체 자막 텍스트를 하나의 문자열로 결합
            full_text = ''
            for entry in transcript:
                full_text += entry['text'] + '\n'
            
            # 자막 텍스트를 텍스트 영역에 표시
            st.text_area('전체 자막', full_text, height=300)
            
            # 요약 버튼
            if full_text.strip():
                with st.spinner('내용을 요약하고 있습니다...'):
                    try:
                        summary = summarize_text(full_text)
                        if summary:
                            st.subheader('요약 내용:')
                            st.write(summary)
                            
                            # 포맷 변환된 요약 표시
                            with st.spinner('요약 내용을 포맷에 맞게 변환하고 있습니다...'):
                                formatted_summary = format_summary_for_thread(summary)
                                st.subheader('쓰레드 형식 요약:')
                                st.markdown(formatted_summary)
                        else:
                            st.error('요약을 생성하는데 실패했습니다.')
                    except Exception as e:
                        st.error(f'요약 처리 중 오류가 발생했습니다: {str(e)}')
            else:
                st.warning('요약할 텍스트가 없습니다.')
            
            # CSV 다운로드 버튼
            st.download_button(
                label="자막 다운로드 (TXT)",
                data=full_text,
                file_name="youtube_transcript.txt",
                mime="text/plain"
            )
        else:
            st.error('자막을 가져올 수 없습니다. 해당 동영상에 자막이 없거나 접근이 제한되어 있을 수 있습니다.')
    else:
        st.error('올바른 YouTube URL을 입력해주세요.')
elif search_button and not youtube_url:
    st.warning('YouTube URL을 입력해주세요.') 