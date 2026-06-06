from pysentimiento import create_analyzer

_emotion_analyzer = None
_sentiment_analyzer = None

def get_emotion_analyzer():
    global _emotion_analyzer
    if _emotion_analyzer is None:
        _emotion_analyzer = create_analyzer(task="emotion", lang="es")
    return _emotion_analyzer

def get_sentiment_analyzer():
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = create_analyzer(task="sentiment", lang="es")
    return _sentiment_analyzer

def analyze_text(text: str):
    emotion_analyzer = get_emotion_analyzer()
    sentiment_analyzer = get_sentiment_analyzer()
    emotion_result = emotion_analyzer.predict(text)
    sentiment_result = sentiment_analyzer.predict(text)
    return {
        "emotion": emotion_result.output,
        "emotion_probs": emotion_result.probs,
        "sentiment": sentiment_result.output,
        "sentiment_probs": sentiment_result.probs
    }

if __name__ == "__main__":
    test_text = "¡Ayuda! Hay un incendio en mi casa, estoy muy asustado."
    result = analyze_text(test_text)
    print(result)