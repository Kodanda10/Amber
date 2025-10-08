declare module 'sentiment' {
  interface SentimentAnalysisResult {
    score: number;
    comparative: number;
    tokens: string[];
    words: string[];
    positive: string[];
    negative: string[];
  }

  class Sentiment {
    analyze(input: string): SentimentAnalysisResult;
  }

  export default Sentiment;
}
