import React from 'react';
import Image from 'next/image';
import type { SocialMediaPost } from '@/types';
import { Sentiment, VerificationStatus, Platform } from '@/types';
import { PLATFORM_ICONS } from '@/data/mockData';
import { format_date_in_hindi, getLanguageLabel } from '@/utils/localization';

interface PostCardProps {
  post: SocialMediaPost;
}

const sentimentColors: Record<Sentiment, string> = {
  [Sentiment.Positive]: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  [Sentiment.Negative]: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  [Sentiment.Neutral]: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

const verificationColors: Record<VerificationStatus, string> = {
  [VerificationStatus.Verified]: 'border-blue-500',
  [VerificationStatus.NeedsReview]: 'border-yellow-500',
  [VerificationStatus.Unverified]: 'border-red-500',
};

const platformTextColors: Record<Platform, string> = {
  [Platform.Twitter]: 'text-blue-400',
  [Platform.Facebook]: 'text-blue-600',
  [Platform.Instagram]: 'text-pink-500',
  [Platform.News]: 'text-indigo-500',
};

const getRelativeTime = (timestamp: string) => {
  const target = new Date(timestamp).getTime();
  const now = Date.now();
  const diffInSeconds = Math.round((target - now) / 1000);

  const divisions = [
    { amount: 60, unit: 'second' as const },
    { amount: 60, unit: 'minute' as const },
    { amount: 24, unit: 'hour' as const },
    { amount: 7, unit: 'day' as const },
    { amount: 4.34524, unit: 'week' as const },
    { amount: 12, unit: 'month' as const },
    { amount: Number.POSITIVE_INFINITY, unit: 'year' as const },
  ];

  let duration = diffInSeconds;
  let unit: Intl.RelativeTimeFormatUnit = 'second';

  for (const division of divisions) {
    if (Math.abs(duration) < division.amount) {
      unit = division.unit;
      break;
    }
    duration /= division.amount;
  }

  const formatter = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  return formatter.format(Math.round(duration), unit);
};

export const PostCard: React.FC<PostCardProps> = ({ post }) => {
  const Icon = PLATFORM_ICONS[post.platform];
  const timeAgo = getRelativeTime(post.timestamp);
  const title = post.metrics.title ?? post.leaderName;
  const link = post.metrics.link;
  const avatarUrl = post.metrics.avatarUrl;
  const mediaUrl = post.metrics.mediaUrl;
  const languageLabel = getLanguageLabel(post.metrics.language);
  const isHindi = languageLabel === 'हिन्दी';
  const hindiDate = isHindi ? format_date_in_hindi(new Date(post.timestamp)) : null;
  const timestampLabel = hindiDate ?? timeAgo;
  const timestampTestId = isHindi ? 'hindi-date-badge' : 'relative-time';

  return (
    <article
      className={`flex gap-4 p-5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 shadow-sm hover:shadow-md transition-shadow duration-200 border-l-4 ${verificationColors[post.verificationStatus]}`}
    >
      <div className="flex-shrink-0">
        {avatarUrl ? (
          <Image
            src={avatarUrl}
            alt={`${post.leaderName} profile photo`}
            width={48}
            height={48}
            className="h-12 w-12 rounded-full object-cover border border-gray-200 dark:border-gray-700"
            unoptimized
            data-testid="post-avatar"
          />
        ) : (
          <div
            className="h-12 w-12 rounded-full bg-indigo-500 text-white flex items-center justify-center font-semibold"
            data-testid="post-avatar-fallback"
          >
            {post.leaderName.charAt(0)}
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <header className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-gray-900 dark:text-gray-100 truncate">{post.leaderName}</span>
              {Icon && <Icon className={`h-4 w-4 ${platformTextColors[post.platform]}`} />}
              {languageLabel && (
                <span className="text-[10px] font-medium uppercase tracking-wider rounded-full bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 px-2 py-0.5">
                  {languageLabel}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              posted on {post.platform} •{' '}
              <span data-testid={timestampTestId}>{timestampLabel}</span>
            </p>
          </div>
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${sentimentColors[post.sentiment]}`}>{post.sentiment}</span>
        </header>

        <div className="mt-3 space-y-2">
          {title && (
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-50 leading-snug">
              {link ? (
                <a href={link} target="_blank" rel="noopener noreferrer" className="hover:underline">
                  {title}
                </a>
              ) : (
                title
              )}
            </h3>
          )}
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
            {post.content}
          </p>
          {post.metrics.source && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Source: {post.metrics.source}
            </p>
          )}
          {mediaUrl && (
            <div className="pt-1">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={mediaUrl}
                alt={`Graph media for ${post.leaderName}`}
                className="max-h-80 w-full rounded-lg object-cover"
                data-testid="post-media"
              />
            </div>
          )}
        </div>
      </div>
    </article>
  );
};
