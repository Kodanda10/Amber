export enum Platform {
	Twitter = 'Twitter',
	Facebook = 'Facebook',
	Instagram = 'Instagram',
	News = 'News',
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
	createdAt?: string;
	avatarUrl?: string;
}

export interface PostMetrics {
	likes: number;
	comments: number;
	shares: number;
	source?: string;
	origin?: string;
	link?: string;
	title?: string;
	avatarUrl?: string;
	language?: string;
	firstSeenAt?: string;
	lastSeenAt?: string;
	revision?: number;
	mediaUrl?: string;
	platformPostId?: string;
	sentimentScore?: number;
	hash?: string;
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

export interface ReviewItem {
	id: string;
	postId: string;
	state: string; // 'pending' | 'approved' | 'rejected'
	notes?: string | null;
	reviewer?: string | null;
	updatedAt?: string | null;
	post?: SocialMediaPost;
}

export type View = 'dashboard' | 'leaders' | 'review';
