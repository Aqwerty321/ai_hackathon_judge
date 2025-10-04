import React, { useState } from 'react';
import Link from "next/link";
import { ThemeToggle } from '@/components/components-theme-toggle';
import { Heart, Menu, X } from "lucide-react";
import { LinkProps } from 'next/link';


interface NavLinkProps extends Pick<LinkProps, 'href'> {
  children: React.ReactNode;
}

function NavLink({ href, children }: NavLinkProps) {
  return (
    <Link className="flex items-center text-sm font-medium hover:underline underline-offset-4 py-2" href={href}>
      {children}
    </Link>
  );
}

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="px-4 lg:px-6 h-14 flex items-center fixed top-0 left-0 right-0 z-10 bg-white shadow-md dark:bg-gray-800">
      <Link className="flex items-center justify-center" href="#">
        <span className="ml-2 text-2xl font-bold">FoodShare</span>
        <Heart className="h-6 w-6 text-red-500 ml-2" />
      </Link>
      <nav className="ml-auto hidden md:flex gap-4 sm:gap-6">
        <ThemeToggle />
        <NavLink href="#about">About</NavLink>
        <NavLink href="#educational-resources">Resources</NavLink>
        <NavLink href="#meet-our-team">Contact</NavLink>
        <NavLink href="../user-auth?tab=login">Login</NavLink>
      </nav>
      <button onClick={toggleMenu} className="ml-auto md:hidden">
        {isMenuOpen ? <X /> : <Menu />}
      </button>
      {isMenuOpen && (
        <div className="absolute top-14 left-0 right-0 bg-white dark:bg-gray-800 shadow-md">
          <nav className="flex flex-col items-center py-4">
            <ThemeToggle />
            <NavLink href="#about">About</NavLink>
            <NavLink href="#educational-resources">Resources</NavLink>
            <NavLink href="#meet-our-team">Contact</NavLink>
            <NavLink href="../user-auth?tab=login">Login</NavLink>
          </nav>
        </div>
      )}
    </header>
  );
}