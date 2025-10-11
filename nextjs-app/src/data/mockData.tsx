import React, { type FC, type SVGProps } from 'react';
import type { Leader } from '@/types';
import { Platform, VerificationStatus } from '@/types';

export const INITIAL_LEADERS: Leader[] = [
  {
    id: 'leader-1',
    name: 'Vishnu Deo Sai',
    handles: { facebook: '@vishnudeosai1' },
    trackingTopics: ['tribal welfare', 'state development', 'governance'],
  },
  {
    id: 'leader-2',
    name: 'Laxmi Rajwade',
    handles: { facebook: '@laxmirajwadebjp' },
    trackingTopics: ['women empowerment', 'public health', 'local issues'],
  },
  {
    id: 'leader-3',
    name: 'Ramvichar Netam',
    handles: { facebook: '@RamvicharNetamB.J.P' },
    trackingTopics: ['agriculture', 'rural development', 'policy making'],
  },
  {
    id: 'leader-4',
    name: 'O. P. Choudhary',
    handles: { facebook: '@OPChoudhary.India' },
    trackingTopics: ['education reform', 'finance', 'urban development'],
  },
  {
    id: 'leader-5',
    name: 'Lakhan Lal Dewangan',
    handles: { facebook: '@lakhanlal.dewangan' },
    trackingTopics: ['commerce', 'industry', 'economic growth'],
  },
  {
    id: 'leader-6',
    name: 'Shyam Bihari Jaiswal',
    handles: { facebook: '@sbjaiswalbjp' },
    trackingTopics: ['public health', 'family welfare', 'medical education'],
  },
  {
    id: 'leader-7',
    name: 'Arun Sao',
    handles: { facebook: '@arunsaobjp' },
    trackingTopics: ['public works', 'law and order', 'state infrastructure'],
  },
  {
    id: 'leader-8',
    name: 'Tank Ram Verma',
    handles: { facebook: '@tankramvermaofficial' },
    trackingTopics: ['sports', 'youth affairs', 'skill development'],
  },
  {
    id: 'leader-9',
    name: 'Dayaldas Baghel',
    handles: { facebook: '@Dayaldasbaghel70' },
    trackingTopics: ['food and civil supplies', 'consumer protection', 'local governance'],
  },
  {
    id: 'leader-10',
    name: 'Vijay Sharma',
    handles: { facebook: '@vijayratancg' },
    trackingTopics: ['home affairs', 'jail administration', 'technical education'],
  },
  {
    id: 'leader-11',
    name: 'Kedar Kashyap',
    handles: { facebook: '@kedarkashyapofficial' },
    trackingTopics: ['forests', 'climate change', 'water resources'],
  },
  {
    id: 'leader-12',
    name: 'Brijmohan Agrawal',
    handles: { facebook: '@brijmohan.ag' },
    trackingTopics: ['public works', 'transport', 'legislative affairs'],
  },
];

export const VERIFICATION_STATUSES = [
  VerificationStatus.Verified,
  VerificationStatus.NeedsReview,
  VerificationStatus.Unverified,
];


const buildIcon = (path: string): FC<SVGProps<SVGSVGElement>> => {
  const Icon: FC<SVGProps<SVGSVGElement>> = ({ className, ...rest }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" {...rest}>
      <path d={path} />
    </svg>
  );

  Icon.displayName = 'PlatformIcon';
  return Icon;
};

const TwitterIcon = buildIcon(
  'M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z'
);
const FacebookIcon = buildIcon(
  'M22 12c0-5.523-4.477-10-10-10S2 6.477 2 12c0 4.991 3.657 9.128 8.438 9.878v-6.987h-2.54V12h2.54V9.797c0-2.506 1.492-3.89 3.777-3.89 1.094 0 2.238.195 2.238.195v2.46h-1.26c-1.243 0-1.63.771-1.63 1.562V12h2.773l-.443 2.89h-2.33v6.988C18.343 21.128 22 16.991 22 12z'
);
const InstagramIcon = buildIcon(
  'M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.85s-.011 3.584-.069 4.85c-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07s-3.584-.012-4.85-.07c-3.252-.148-4.771-1.691-4.919-4.919-.058-1.265-.069-1.645-.069-4.85s.011-3.584.069-4.85c.149-3.225 1.664-4.771 4.919-4.919 1.266-.057 1.644-.069 4.85-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948s.014 3.667.072 4.947c.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072s3.667-.014 4.947-.072c4.358-.2 6.78-2.618 6.98-6.98.059-1.281.073-1.689.073-4.948s-.014-3.667-.072-4.947c-.2-4.358-2.618-6.78-6.98-6.98-1.281-.058-1.689-.072-4.948-.072zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.162 6.162 6.162 6.162-2.759 6.162-6.162-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4s1.791-4 4-4 4 1.79 4 4-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44 1.441-.645 1.441-1.44-.645-1.44-1.441-1.44z'
);

const NewsIcon = buildIcon(
  'M4 4h16v16H4zM8 8h8M8 12h10M8 16h6'
);

export const PLATFORM_ICONS: Record<Platform, FC<SVGProps<SVGSVGElement>>> = {
  [Platform.Twitter]: TwitterIcon,
  [Platform.Facebook]: FacebookIcon,
  [Platform.Instagram]: InstagramIcon,
  [Platform.News]: NewsIcon,
};
