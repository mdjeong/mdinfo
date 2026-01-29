'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navigation() {
    const pathname = usePathname();

    return (
        <nav className="category-tabs" role="navigation" aria-label="카테고리 네비게이션">
            <Link
                href="/"
                className={pathname === '/' ? 'active' : ''}
                aria-current={pathname === '/' ? 'page' : undefined}
            >
                전체
            </Link>
            <Link
                href="/news"
                className={pathname === '/news' ? 'active' : ''}
                aria-current={pathname === '/news' ? 'page' : undefined}
            >
                뉴스
            </Link>
            <Link
                href="/papers"
                className={pathname === '/papers' ? 'active' : ''}
                aria-current={pathname === '/papers' ? 'page' : undefined}
            >
                논문
            </Link>
        </nav>
    );
}
