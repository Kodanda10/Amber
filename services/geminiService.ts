import { GoogleGenAI, Type } from "@google/genai";
import type { Leader, SocialMediaPost, Platform, Sentiment, VerificationStatus } from '../types';
import { VERIFICATION_STATUSES } from "../constants";

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  throw new Error("API_KEY environment variable is not set.");
}

const ai = new GoogleGenAI({ apiKey: API_KEY });

const postGenerationSchema = {
  type: Type.ARRAY,
  items: {
    type: Type.OBJECT,
    properties: {
      platform: {
        type: Type.STRING,
        enum: ['Facebook'],
        description: 'The social media platform.',
      },
      content: {
        type: Type.STRING,
        description: 'The content of the social media post. Should be realistic for a political figure.',
      },
      sentiment: {
        type: Type.STRING,
        enum: ['Positive', 'Negative', 'Neutral'],
        description: 'The overall sentiment of the post.',
      },
      metrics: {
        type: Type.OBJECT,
        properties: {
          likes: { type: Type.INTEGER, description: 'A realistic number of likes, between 50 and 50000.' },
          comments: { type: Type.INTEGER, description: 'A realistic number of comments, between 10 and 5000.' },
          shares: { type: Type.INTEGER, description: 'A realistic number of shares or retweets, between 20 and 10000.' },
        },
        required: ['likes', 'comments', 'shares'],
      },
    },
    required: ['platform', 'content', 'sentiment', 'metrics'],
  },
};

export const generateSocialMediaPosts = async (leader: Leader): Promise<SocialMediaPost[]> => {
  try {
    const prompt = `Generate 5 recent, realistic Facebook posts for a political leader named ${leader.name}. The posts should be on topics like: ${leader.trackingTopics.join(', ')}. Ensure the content reflects typical political communications.`;

    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: postGenerationSchema,
      },
    });

    const jsonText = response.text.trim();
    const generatedData = JSON.parse(jsonText);

    if (!Array.isArray(generatedData)) {
      console.error("Gemini API did not return an array:", generatedData);
      return [];
    }

    return generatedData.map((item: any, index: number) => ({
      id: `${leader.id}-${Date.now()}-${index}`,
      leaderId: leader.id,
      leaderName: leader.name,
      platform: item.platform as Platform,
      content: item.content,
      timestamp: new Date(Date.now() - Math.random() * 1000 * 3600 * 24 * 7).toISOString(),
      sentiment: item.sentiment as Sentiment,
      metrics: item.metrics,
      verificationStatus: VERIFICATION_STATUSES[Math.floor(Math.random() * VERIFICATION_STATUSES.length)] as VerificationStatus,
    }));
  } catch (error) {
    console.error("Error generating social media posts:", error);
    throw new Error("Failed to fetch data from Gemini API.");
  }
};