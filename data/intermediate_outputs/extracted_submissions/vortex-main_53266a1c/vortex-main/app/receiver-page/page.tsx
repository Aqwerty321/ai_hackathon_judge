'use client'

import React, { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Separator } from "@/components/ui/separator"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Bell, Settings, LogOut, Plus, MapPin, Phone, Mail, Search, Star, ThumbsUp } from 'lucide-react'
import Link from 'next/link'
import MapView from '../shared/map-view/MapView'
import { ThemeToggle } from '@/components/components-theme-toggle'
import '@/app/globals.css';

export default function ReceiverPage() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b">
        <div className="container flex items-center justify-between h-16 px-4">
          <Link href="/" className="flex items-center">
            <span className="text-2xl font-bold">FoodShare</span>
          </Link>
          <nav className="flex items-center gap-4">
          <ThemeToggle />
            <Button variant="ghost" size="icon">
              <Bell className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <Settings className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <Link href="../user-auth">
                <LogOut className="h-5 w-5" />
              </Link>            
            </Button>
            <Avatar onClick={() => setActiveTab('profile')} className="cursor-pointer">
              <AvatarImage src="/placeholder.svg?height=32&width=32" alt="User" />
              <AvatarFallback>JD</AvatarFallback>
            </Avatar>
          </nav>
        </div>
      </header>
      <div className="flex-1 container px-4 py-6 grid gap-6 md:grid-cols-[200px_1fr]">
        <aside className="hidden md:block">
          <nav className="flex flex-col gap-2">
            <Button variant={activeTab === 'dashboard' ? 'secondary' : 'ghost'} className="justify-start" onClick={() => setActiveTab('dashboard')}>
              Dashboard
            </Button>
            <Button variant={activeTab === 'search' ? 'secondary' : 'ghost'} className="justify-start" onClick={() => setActiveTab('search')}>
              Search Donations
            </Button>
            <Button variant={activeTab === 'feedback' ? 'secondary' : 'ghost'} className="justify-start" onClick={() => setActiveTab('feedback')}>
              View Feedback
            </Button>
            <Button variant={activeTab === 'map' ? 'secondary' : 'ghost'} className="justify-start" onClick={() => setActiveTab('map')}>
              Map
            </Button>
          </nav>
        </aside>
        <main className="space-y-6">
          <h2 className="text-3xl font-bold tracking-tight">Welcome, Local Food Bank</h2>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList className="md:hidden">
              <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
              <TabsTrigger value="search">Search</TabsTrigger>
              <TabsTrigger value="feedback">Feedback</TabsTrigger>
              <TabsTrigger value="profile">Profile</TabsTrigger>
            </TabsList>
            <TabsContent value="dashboard" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Received</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">50</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">People Served</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">1000</div>
                  </CardContent>
                </Card>
              </div>
              <Card>
                <CardHeader>
                  <CardTitle>My Requests</CardTitle>
                  <CardDescription>View and manage your food requests.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Food Needed</TableHead>
                        <TableHead>Quantity</TableHead>
                        <TableHead>Needed By</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>Non-perishable items</TableCell>
                        <TableCell>100 servings</TableCell>
                        <TableCell>2023-07-15</TableCell>
                        <TableCell><Badge>Fulfilled</Badge></TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Fresh produce</TableCell>
                        <TableCell>50 servings</TableCell>
                        <TableCell>2023-07-10</TableCell>
                        <TableCell><Badge variant="secondary">Fulfilled</Badge></TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Canned goods</TableCell>
                        <TableCell>200 servings</TableCell>
                        <TableCell>2023-07-20</TableCell>
                        <TableCell><Badge>Fulfilled</Badge></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="search" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Search Donations</CardTitle>
                  <CardDescription>Find available food donations in your area.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-6 md:grid-cols-[300px_1fr]">
                    <div className="space-y-6">
                      <div className="space-y-2">
                        <Label htmlFor="location">Location</Label>
                        <div className="relative">
                          <MapPin className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                          <Input id="location" placeholder="Enter your location" className="pl-8" />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="radius">Search Radius (km)</Label>
                        <Slider
                          id="radius"
                          min={1}
                          max={50}
                          step={1}
                          defaultValue={[10]}
                          className="w-full"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="food-type">Food Type</Label>
                        <Select>
                          <SelectTrigger id="food-type">
                            <SelectValue placeholder="Select food type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Types</SelectItem>
                            <SelectItem value="prepared">Prepared Meals</SelectItem>
                            <SelectItem value="produce">Fresh Produce</SelectItem>
                            <SelectItem value="canned">Canned Goods</SelectItem>
                            <SelectItem value="baked">Baked Goods</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="expiry">Expiry</Label>
                        <Select>
                          <SelectTrigger id="expiry">
                            <SelectValue placeholder="Select expiry range" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All</SelectItem>
                            <SelectItem value="today">Today</SelectItem>
                            <SelectItem value="tomorrow">Tomorrow</SelectItem>
                            <SelectItem value="week">This Week</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button className="btn w-full">Apply Filters</Button>
                    </div>
                    <div className="space-y-6">
                      <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input placeholder="Search donations" className="pl-8" />
                      </div>
                      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {[...Array(6)].map((_, i) => (
                          <div key={i} className="border rounded-lg p-4 space-y-2">
                            <h3 className="font-semibold">Fresh Vegetables</h3>
                            <p className="text-sm text-muted-foreground">Expiry: 2 days</p>
                            <p className="text-sm">Quantity: Enough for 10-15 people</p>
                            <p className="text-sm flex items-center">
                              <MapPin className="h-4 w-4 mr-1" />
                              2.5 km away
                            </p>
                            <Button asChild className="btn w-full mt-2">
                              <Link href="#">View Details</Link>
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="feedback" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Received Feedback</CardTitle>
                  <CardDescription>View feedback from donors about your organization.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between items-center mb-6">
                    <Select>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Filter by rating" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Ratings</SelectItem>
                        <SelectItem value="5">5 Stars</SelectItem>
                        <SelectItem value="4">4 Stars</SelectItem>
                        <SelectItem value="3">3 Stars</SelectItem>
                        <SelectItem value="2">2 Stars</SelectItem>
                        <SelectItem value="1">1 Star</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button className="btn" variant="outline">Export Feedback</Button>
                  </div>
                  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {[...Array(6)].map((_, i) => (
                      <Card key={i}>
                        <CardHeader>
                          <CardTitle className="flex justify-between items-center">
                            <span>Donation #{1000 + i}</span>
                            <div className="flex">
                              {[...Array(5)].map((_, j) => (
                                <Star
                                  key={j}
                                  className={`h-5 w-5 ${
                                    j < 4 ? "text-yellow-400 fill-yellow-400" : "text-muted-foreground"
                                  }`}
                                />
                              ))}
                            </div>
                          </CardTitle>
                          <CardDescription>Received on {new Date().toLocaleDateString()}</CardDescription>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm mb-2">
                            "The food quality was excellent, and it helped feed many families in need. Thank you for your
                            generous donation!"
                          </p>
                          <div className="flex items-center justify-between text-sm text-muted-foreground">
                            <span>Food Quality: Excellent</span>
                            <div className="flex items-center">
                              <ThumbsUp className="h-4 w-4 mr-1" />
                              <span>Helpful</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="profile" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Profile Information</CardTitle>
                  <CardDescription>Manage your receiver profile details.</CardDescription>
                </CardHeader>
                <CardContent>
                  <form>
                    <div className="grid gap-4">
                      <div className="flex items-center gap-4">
                        <Avatar className="w-20 h-20">
                          <AvatarImage src="/placeholder.svg?height=80&width=80" alt="Local Food Bank" />
                          <AvatarFallback>LF</AvatarFallback>
                        </Avatar>
                        <Button className="btn">Change Avatar</Button>
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="organization-name">Organization Name</Label>
                        <Input id="organization-name" value="Local Food Bank" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="organization-type">Organization Type</Label>
                        <Select>
                          <SelectTrigger id="organization-type">
                            <SelectValue placeholder="Select organization type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="food-bank">Food Bank</SelectItem>
                            <SelectItem value="shelter">Shelter</SelectItem>
                            <SelectItem value="community-center">Community Center</SelectItem>
                            <SelectItem value="other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" type="email" value="contact@localfoodbank.org" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="phone">Phone</Label>
                        <Input id="phone" type="tel" value="+1 (555) 987-6543" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="address">Address</Label>
                        <Textarea id="address" value="456 Charity Lane, Helptown, USA" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="description">Organization Description</Label>
                        <Textarea id="description" value="We are dedicated to eliminating hunger in our local community by providing nutritious meals to those in need." />
                      </div>
                    </div>
                  </form>
                </CardContent>
                <CardFooter>
                  <Button className="btn">Save Changes</Button>
                </CardFooter>
              </Card>
            </TabsContent>
            <TabsContent value="map" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Map View</CardTitle>
                  <CardDescription>View nearby receivers and donations on the map.</CardDescription>
                </CardHeader>
                <CardContent>
                  <MapView userType="donor" />
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </main>
      </div>
    </div>
  )
}