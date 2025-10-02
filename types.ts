
export enum Platform {
  Twitter = 'Twitter',
  Facebook = 'Facebook',
  Instagram = 'Instagram',
}

export enum Sentiment {
  Positive = 'Positive',
  Negative = 'Negative',
  Neutral = 'Neutral',
}

export enum VerificationStatus {
  Verified = 'Verified',
  NeedsReview = 'Needs Review',
  Unverified = 'Unverified',
}

export interface SocialMediaHandles {
  twitter?: string;
  facebook?: string;
  instagram?: string;
}

export interface Leader {
  id: string;
  name: string;
  handles: SocialMediaHandles;
  trackingTopics: string[];
}

export interface PostMetrics {
  likes: number;
  comments: number;
  shares: number;
}

export interface SocialMediaPost {
  id: string;
  leaderId: string;
  leaderName: string;
  platform: Platform;
  content: string;
  timestamp: string;
  sentiment: Sentiment;
  metrics: PostMetrics;
  verificationStatus: VerificationStatus;
}

export interface ReportData {
  totalPosts: number;
  totalLeaders: number;
  posts: SocialMediaPost[];
}
