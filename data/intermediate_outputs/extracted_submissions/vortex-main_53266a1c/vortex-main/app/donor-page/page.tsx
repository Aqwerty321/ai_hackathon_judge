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
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Slider } from "@/components/ui/slider"
import { Bell, Settings, LogOut, Plus, MapPin, Phone, Mail, Search, Users, Star } from 'lucide-react'
import Link from 'next/link'
import MapView from '../shared/map-view/MapView'
import { ThemeToggle } from '@/components/components-theme-toggle'
import '@/app/globals.css';

export default function DonorPage() {
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
            <Button variant={activeTab === 'donations' ? 'secondary' : 'ghost'} className="justify-start" onClick={() => setActiveTab('donations')}>
              My Donations
            </Button>
            <Button variant={activeTab === 'search' ? 'secondary' : 'ghost'} className="justify-start" onClick={() => setActiveTab('search')}>
              Search Receivers
            </Button>
            <Button variant={activeTab === 'feedback' ? 'secondary' : 'ghost'} className="justify-start" onClick={() => setActiveTab('feedback')}>
              Leave Feedback
            </Button>
            <Button variant={activeTab === 'map' ? 'secondary' : 'ghost'} className="justify-start" onClick={() => setActiveTab('map')}>
              Map
            </Button>
          </nav>
        </aside>
        <main className="space-y-6">
          <h2 className="text-3xl font-bold tracking-tight">Welcome, John Doe</h2>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <TabsList className="md:hidden">
              <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
              <TabsTrigger value="donations">My Donations</TabsTrigger>
              <TabsTrigger value="search">Search</TabsTrigger>
              <TabsTrigger value="feedback">Feedback</TabsTrigger>
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="map">Map</TabsTrigger>
            </TabsList>
            <TabsContent value="dashboard" className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Donations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">25</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">People Helped</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">500</div>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Active Listings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">3</div>
                  </CardContent>
                </Card>
              </div>
              <Card>
                <CardHeader>
                  <CardTitle>Create New Donation</CardTitle>
                  <CardDescription>List a new food donation for those in need.</CardDescription>
                </CardHeader>
                <CardContent>
                  <form>
                    <div className="grid gap-4">
                      <div className="grid gap-2">
                        <Label htmlFor="food-description">Food Description</Label>
                        <Textarea id="food-description" placeholder="Describe the food you're donating" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="quantity">Quantity (servings)</Label>
                        <Input id="quantity" type="number" min="1" placeholder="Enter number of servings" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="expiry">Expiry Date and Time</Label>
                        <Input id="expiry" type="datetime-local" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="pickup-location">Pickup Location</Label>
                        <Input id="pickup-location" placeholder="Enter pickup address" />
                      </div>
                    </div>
                  </form>
                </CardContent>
                <CardFooter>
                  <Button className="w-full btn">
                    <Plus className="mr-2 h-4 w-4" /> Create Donation
                  </Button>
                </CardFooter>
              </Card>
            </TabsContent>
            <TabsContent value="donations" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>My Donations</CardTitle>
                  <CardDescription>View and manage your food donations.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Food Description</TableHead>
                        <TableHead>Quantity</TableHead>
                        <TableHead>Expiry Date</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow>
                        <TableCell>Assorted sandwiches</TableCell>
                        <TableCell>50 servings</TableCell>
                        <TableCell>2023-06-30</TableCell>
                        <TableCell><Badge className="btn">Active</Badge></TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Fresh vegetables</TableCell>
                        <TableCell>30 servings</TableCell>
                        <TableCell>2023-06-28</TableCell>
                        <TableCell><Badge variant="secondary">Claimed</Badge></TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Canned goods</TableCell>
                        <TableCell>100 servings</TableCell>
                        <TableCell>2023-07-15</TableCell>
                        <TableCell><Badge className="btn">Active</Badge></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="search" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Search Receivers</CardTitle>
                  <CardDescription>Find receivers for your donations.</CardDescription>
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
                        <Label htmlFor="organization-type">Organization Type</Label>
                        <Select>
                          <SelectTrigger id="organization-type">
                            <SelectValue placeholder="Select organization type" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Types</SelectItem>
                            <SelectItem value="shelter">Homeless Shelter</SelectItem>
                            <SelectItem value="foodbank">Food Bank</SelectItem>
                            <SelectItem value="school">School</SelectItem>
                            <SelectItem value="community">Community Center</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="capacity">Capacity</Label>
                        <Select>
                          <SelectTrigger id="capacity">
                            <SelectValue placeholder="Select capacity range" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All</SelectItem>
                            <SelectItem value="small">Small (1-50 people)</SelectItem>
                            <SelectItem value="medium">Medium (51-200 people)</SelectItem>
                            <SelectItem value="large">Large (200+ people)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button className="btn w-full">Apply Filters</Button>
                    </div>
                    <div className="space-y-6">
                      <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input placeholder="Search receivers" className="pl-8" />
                      </div>
                      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                        {[...Array(6)].map((_, i) => (
                          <div key={i} className="border rounded-lg p-4 space-y-2">
                            <h3 className="font-semibold">Community Food Center</h3>
                            <p className="text-sm text-muted-foreground">Type: Food Bank</p>
                            <p className="text-sm flex items-center">
                              <Users className="h-4 w-4 mr-1" />
                              Capacity: 100-150 people
                            </p>
                            <p className="text-sm flex items-center">
                              <MapPin className="h-4 w-4 mr-1" />
                              3.2 km away
                            </p>
                            <Button asChild className="w-full mt-2 btn">
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
                  <CardTitle>Leave Feedback</CardTitle>
                  <CardDescription>Share your experience about the recent donation you received</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="donation-id">Donation ID</Label>
                    <Input id="donation-id" placeholder="Enter the donation ID" />
                  </div>
                  <div className="space-y-2">
                    <Label>Overall Rating</Label>
                    <RadioGroup defaultValue="3" className="flex space-x-1">
                      {[1, 2, 3, 4, 5].map((value) => (
                        <Label
                          key={value}
                          className="cursor-pointer p-2 rounded-full hover:bg-muted"
                          htmlFor={`rating-${value}`}
                        >
                          <RadioGroupItem
                            value={value.toString()}
                            id={`rating-${value}`}
                            className="sr-only"
                          />
                          <Star
                            className={`h-6 w-6 ${
                              value <= 3 ? "text-yellow-400 fill-yellow-400" : "text-muted-foreground"
                            }`}
                          />
                        </Label>
                      ))}
                    </RadioGroup>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="food-quality">Food Quality</Label>
                    <RadioGroup defaultValue="good" className="flex space-x-4">
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="poor" id="food-quality-poor" />
                        <Label htmlFor="food-quality-poor">Poor</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="fair" id="food-quality-fair" />
                        <Label htmlFor="food-quality-fair">Fair</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="good" id="food-quality-good" />
                        <Label htmlFor="food-quality-good">Good</Label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <RadioGroupItem value="excellent" id="food-quality-excellent" />
                        <Label htmlFor="food-quality-excellent">Excellent</Label>
                      </div>
                    </RadioGroup>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="comments">Additional Comments</Label>
                    <Textarea id="comments" placeholder="Share your thoughts about the donation" />
                  </div>
                </CardContent>
                <CardFooter>
                  <Button className="w-full btn">Submit Feedback</Button>
                </CardFooter>
              </Card>
            </TabsContent>
            <TabsContent value="profile" className="space-y-4">
            <Card>
                <CardHeader>
                  <CardTitle>Profile Information</CardTitle>
                  <CardDescription>Manage your donor profile details.</CardDescription>
                </CardHeader>
                <CardContent>
                  <form>
                    <div className="grid gap-4">
                      <div className="flex items-center gap-4">
                        <Avatar className="w-20 h-20">
                          <AvatarImage src="/placeholder.svg?height=80&width=80" alt="John Doe" />
                          <AvatarFallback>JD</AvatarFallback>
                        </Avatar>
                        <Button className="btn">Change Avatar</Button>
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="full-name">Full Name</Label>
                        <Input id="full-name" value="John Doe" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="email">Email</Label>
                        <Input id="email" type="email" value="john.doe@example.com" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="phone">Phone</Label>
                        <Input id="phone" type="tel" value="+1 (555) 123-4567" />
                      </div>
                      <div className="grid gap-2">
                        <Label htmlFor="address">Address</Label>
                        <Textarea id="address" value="123 Main St, Anytown, USA" />
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