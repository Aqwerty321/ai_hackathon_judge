'use client';
import { motion, useAnimation } from 'framer-motion';
import { useEffect, useState } from 'react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import Navbar from "@/components/ui/navbar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { AlertTriangle, ArrowRight, CheckCircle2, Gift, Github, Heart, HelpCircle, Leaf, Linkedin, MapPin, ShieldCheck, Thermometer, Twitter, Users } from "lucide-react"
import Image from "next/image"
import Link from "next/link"
import { TypeAnimation } from 'react-type-animation';
import { ThemeToggle } from '@/components/components-theme-toggle'
import '@/app/globals.css';

export default function LandingPageComponent() {
  const headingText = "Bridging Tables, Nourishing Lives";

  const teamMembers = [
    {
      name: "Aryan Shah",
      role: "Frontend Developer",
      bio: "A creative frontend developer passionate about building intuitive and dynamic user interfaces that enhance user experience.",
      image: "/images/aryan.jpg",
      github: "https://github.com/alexjohnson",
      linkedin: "https://linkedin.com/in/alexjohnson",
      twitter: "https://twitter.com/alexjohnson",
    },
    {
      name: "Devishi Raizada",
      role: "Backend Developer",
      bio: "A detail-oriented backend developer skilled in creating efficient server-side logic and database management.  ",
      image: "/images/devishi.jpg",
      github: "https://github.com/samanthalee",
      linkedin: "https://linkedin.com/in/samanthalee",
      twitter: "https://twitter.com/samanthalee",
    },
    {
      name: "Eshitaa Chokhani",
      role: "Backend Developer, Web Designer",
      bio: "A versatile backend developer and web designer, combining clean code with beautiful, user-centric designs.",
      image: "/images/eshita.jpg",
      github: "https://github.com/michaelchen",
      linkedin: "https://linkedin.com/in/michaelchen",
      twitter: "https://twitter.com/michaelchen",
    },
    {
      name: "Harshitaa Kashyap",
      role: "Backend Developer",
      bio: "A backend developer dedicated to building robust APIs and scalable systems to handle complex data flows.",
      image: "/images/harshita.jpg",
      github: "https://github.com/emilyrodriguez",
      linkedin: "https://linkedin.com/in/emilyrodriguez",
      twitter: "https://twitter.com/emilyrodriguez",
    },
    {
      name: "Nandini Sarvaiya",
      role: "Backend Developer",
      bio: "A backend developer with a passion for crafting secure and optimized server-side architectures.",
      image: "/images/nandini.jpg",
      github: "https://github.com/davidkim",
      linkedin: "https://linkedin.com/in/davidkim",
      twitter: "https://twitter.com/davidkim",
    },
    {
      name: "Prathamesh Chaudhari",
      role: "Full Stack Developer",
      bio: "A full stack developer who bridges the gap between frontend and backend to deliver seamless, end-to-end solutions.",
      image: "/images/prathamesh.jpg",
      github: "https://github.com/sarahthompson",
      linkedin: "https://linkedin.com/in/sarahthompson",
      twitter: "https://twitter.com/sarahthompson",
    },
  ]

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-r from-blue-100 via-transparent to-transparent dark:from-blue-400 dark:via-transparent dark:to-transparent">
      <Navbar/>
      <main className="flex-1">
        <section className="w-full py-12 md:py-24 lg:py-32 xl:py-48">
          <div className="container px-4 md:px-6">
            <div className="grid gap-6 lg:grid-cols-[1fr_400px] lg:gap-12 xl:grid-cols-[1fr_600px]">
              <div className="flex flex-col justify-center space-y-4">
                <div className="space-y-2">
                <TypeAnimation className='text-3xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none'
      sequence={[ 
        'Bridging Tables, Nourishing Lives',
        1000,
      ]}
      wrapper="span"
      speed={30}
      repeat={Infinity}
    />
    <br/>
    <p className="max-w-[600px] text-gray-500 md:text-xl dark:text-gray-400">
                    We transform surplus food into opportunities, ensuring that excess culinary treasures don’t go to waste but instead find their way to those who will savor them. Join us in our mission to foster community, reduce waste, and create meaningful connections through the simple act of sharing.
                  </p>
                </div>
                <div className="flex flex-col gap-2 min-[400px]:flex-row">
                  <Link
                    className="inline-flex h-10 items-center justify-center rounded-md bg-gray-900 px-8 text-sm font-medium text-gray-50 shadow transition-colors hover:bg-gray-900/90 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:pointer-events-none disabled:opacity-50 dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-50/90 dark:focus-visible:ring-gray-300"
                    href="#"
                  >
                    Get Started
                  </Link>
                  <Link
                    className="inline-flex h-10 items-center justify-center rounded-md border border-gray-200 bg-white px-8 text-sm font-medium shadow-sm transition-colors hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-gray-950 disabled:pointer-events-none disabled:opacity-50 dark:border-gray-800 dark:bg-gray-950 dark:hover:bg-gray-800 dark:hover:text-gray-50 dark:focus-visible:ring-gray-300"
                    href="#"
                  >
                    Learn More
                  </Link>
                </div>
              </div>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="float-animation"
              >
                <Image
                  alt="Hero"
                  className="mx-auto aspect-video overflow-hidden rounded-xl object-cover object-center sm:w-full lg:order-last"
                  height="310"
                  src="/images/illustration.png"
                  width="550"
                />
              </motion.div>
          </div>
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gray-100 dark:bg-gray-800">
          <div className="container px-4 md:px-6">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl text-center mb-12">How It Works</h2>
            <div className="grid gap-6 lg:grid-cols-3 lg:gap-12">
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-900 text-white">
                  <Gift className="h-10 w-10" />
                </div>
                <h3 className="text-xl font-bold">Donate Food</h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Donors can easily list their surplus food, specifying details like quantity, expiry, and delivery options.
                </p>
              </div>
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-900 text-white">
                  <MapPin className="h-10 w-10" />
                </div>
                <h3 className="text-xl font-bold">Find Receivers</h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Our platform matches donors with nearby receivers based on location and food requirements.
                </p>
              </div>
              <div className="flex flex-col items-center space-y-4 text-center">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gray-900 text-white">
                  <Users className="h-10 w-10" />
                </div>
                <h3 className="text-xl font-bold">Make a Difference</h3>
                <p className="text-gray-500 dark:text-gray-400">
                  Track the impact of your donations and see how many people you've helped feed.
                </p>
              </div>
            </div>
          </div>
        </section>
        <section className="w-full py-12 md:py-24 lg:py-32">
          <div className="container px-4 md:px-6">
            <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl text-center mb-12">Get Involved</h2>
            <Tabs className="w-full max-w-3xl mx-auto" defaultValue="donor">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="donor">I Want to Donate</TabsTrigger>
                <TabsTrigger value="receiver">I Need Food</TabsTrigger>
              </TabsList>
              <TabsContent value="donor">
                <div className="space-y-4 mt-6">
                  <div className="space-y-2">
                    <Label htmlFor="location">Your Location</Label>
                    <Input id="location" placeholder="Enter your address" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="food-for">Number of people it can feed</Label>
                    <Input id="food-for" placeholder="e.g. 10-20" />
                  </div>
                  <Link href="../user-auth?tab=donor">
                    <Button className="btn w-full">
                      Register as Donor
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </TabsContent>
              <TabsContent value="receiver">
                <div className="space-y-4 mt-6">
                  <div className="space-y-2">
                    <Label htmlFor="org-name">Organization Name</Label>
                    <Input id="org-name" placeholder="Enter your organization name" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="people-to-feed">Number of People to Feed</Label>
                    <Input id="people-to-feed" placeholder="e.g. 50" />
                  </div>
                  <Link href="../user-auth?tab=receiver">
                    <Button className="btn w-full">
                      Register as Receiver
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </section>
        <section id="about" className="w-full py-12 md:py-24 lg:py-32 bg-gray-100 dark:bg-gray-800">
          <div className="container mx-auto px-4">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold mb-4">About FoodShare</h2>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                {/* We're on a mission to eliminate food waste and hunger by connecting food donors with those in need. */}
              </p>
            </div>

            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3 mb-12">
              <Card>
                <CardHeader>
                  <CardTitle>Our Mission</CardTitle>
                </CardHeader>
                <CardContent>
                  We envision a world free from food waste and hunger! By harnessing technology, we connect generous food donors with those in need, making sharing simple and effective.
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Our Vision</CardTitle>
                </CardHeader>
                <CardContent>
                  Imagine a future where every morsel of surplus food reaches someone in need. We’re striving for a planet where sharing is second nature and sustainability is at the heart of every meal.
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Our Impact</CardTitle>
                </CardHeader>
                <CardContent>
                  Together, we aim to serve thousands of meals and unite generous donors to make a positive impact in communities everywhere. Join us on this journey of kindness and connection!
                </CardContent>
              </Card>
            </div>

            <div className="mb-12">
              <div className="grid gap-8 md:grid-cols-2 items-center">
                <div>
                <h3 className="text-5xl font-bold text-center mb-8">Our Story</h3>
                  <p className="mb-4">
                    FoodShare was inspired by a simple truth: while millions face hunger every day, tons of good food go to waste. As students, we witnessed this paradox firsthand and felt compelled to take action.
                  </p>
                  <p className="mb-4">
                    Driven by our desire for an effective solution, we created a website that connects kind-hearted individuals with those in need, streamlining the food donation process.
                  </p>
                  <p>
                    Right now, FoodShare is an emerging platform, bringing together passionate individuals and organizations dedicated to making a difference, one meal at a time.
                  </p>
                </div>
                <div className="relative h-[300px] md:h-[400px]">
                  <Image
                    src="/images/illustration1.png"
                    alt="FoodShare team working together"
                    layout="fill"
                    objectFit="cover"
                    className="rounded-lg"
                  />
                </div>
              </div>
            </div>

            <section id="meet-our-team" className = "md:pt-20"> 
              <div>
                <h3 className="text-2xl font-bold text-center mb-8">Meet Our Team</h3>
                <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                  {teamMembers.map((member) => (
                    <Card key={member.name}>
                      <CardHeader>
                        <Avatar className="w-24 h-24 mx-auto mb-4">
                          <AvatarImage src={member.image} alt={member.name} />
                          <AvatarFallback>{member.name.split(" ").map((n) => n[0]).join("")}</AvatarFallback>
                        </Avatar>
                        <CardTitle>{member.name}</CardTitle>
                        <CardDescription>{member.role}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm mb-4">{member.bio}</p>
                        <div className="flex justify-center space-x-2">
                          <Button variant="outline" size="icon" asChild>
                            <Link href={member.github}>
                              <Github className="h-4 w-4" />
                              <span className="sr-only">GitHub</span>
                            </Link>
                          </Button>
                          <Button variant="outline" size="icon" asChild>
                            <Link href={member.linkedin}>
                              <Linkedin className="h-4 w-4" />
                              <span className="sr-only">LinkedIn</span>
                            </Link>
                          </Button>
                          <Button variant="outline" size="icon" asChild>
                            <Link href={member.twitter}>
                              <Twitter className="h-4 w-4" />
                              <span className="sr-only">Twitter</span>
                            </Link>
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            </section>

          </div>
        </section>
        <section id="educational-resources" className="w-full py-12 md:py-24 lg:py-32">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-bold mb-6">Educational Resources</h2>
            <Tabs defaultValue="safety" className="space-y-4">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="safety">Food Safety Guidelines</TabsTrigger>
                <TabsTrigger value="best-practices">Best Practices for Donation</TabsTrigger>
                <TabsTrigger value="faq">FAQ</TabsTrigger>
              </TabsList>
              <TabsContent value="safety">
                <Card>
                  <CardHeader>
                    <CardTitle>Food Safety Guidelines</CardTitle>
                    <CardDescription>
                      Ensure the safety and quality of donated food with these important guidelines.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="flex items-start space-x-2">
                        <Thermometer className="h-5 w-5 mt-0.5 text-blue-500" />
                        <div>
                          <h3 className="font-semibold">Temperature Control</h3>
                          <p className="text-sm text-muted-foreground">
                            Keep hot foods above 140°F (60°C) and cold foods below 40°F (4°C).
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-2">
                        <ShieldCheck className="h-5 w-5 mt-0.5 text-green-500" />
                        <div>
                          <h3 className="font-semibold">Packaging Integrity</h3>
                          <p className="text-sm text-muted-foreground">
                            Ensure all packaging is sealed and undamaged to prevent contamination.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-2">
                        <AlertTriangle className="h-5 w-5 mt-0.5 text-yellow-500" />
                        <div>
                          <h3 className="font-semibold">Allergen Labeling</h3>
                          <p className="text-sm text-muted-foreground">
                            Clearly label all known allergens in donated food items.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-2">
                        <Leaf className="h-5 w-5 mt-0.5 text-emerald-500" />
                        <div>
                          <h3 className="font-semibold">Fresh Produce Handling</h3>
                          <p className="text-sm text-muted-foreground">
                            Wash all fruits and vegetables thoroughly before donation.
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-muted p-4 rounded-lg">
                      <h3 className="font-semibold mb-2">Remember:</h3>
                      <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                        <li>Always check expiration dates before donating</li>
                        <li>Do not donate food that has been previously served</li>
                        <li>Transport food in clean, sanitized containers</li>
                        <li>When in doubt about food safety, it's best not to donate</li>
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="best-practices">
                <Card>
                  <CardHeader>
                    <CardTitle>Best Practices for Donation</CardTitle>
                    <CardDescription>
                      Follow these guidelines to make your food donations more effective and impactful.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="flex items-start space-x-2">
                        <CheckCircle2 className="h-5 w-5 mt-0.5 text-green-500" />
                        <div>
                          <h3 className="font-semibold">Quality Check</h3>
                          <p className="text-sm text-muted-foreground">
                            Donate food that you would be willing to eat yourself.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-2">
                        <CheckCircle2 className="h-5 w-5 mt-0.5 text-green-500" />
                        <div>
                          <h3 className="font-semibold">Nutritional Value</h3>
                          <p className="text-sm text-muted-foreground">
                            Focus on donating nutrient-rich, wholesome foods when possible.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-2">
                        <CheckCircle2 className="h-5 w-5 mt-0.5 text-green-500" />
                        <div>
                          <h3 className="font-semibold">Proper Packaging</h3>
                          <p className="text-sm text-muted-foreground">
                            Use clean, sturdy containers that protect food during transport.
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start space-x-2">
                        <CheckCircle2 className="h-5 w-5 mt-0.5 text-green-500" />
                        <div>
                          <h3 className="font-semibold">Clear Labeling</h3>
                          <p className="text-sm text-muted-foreground">
                            Label all items with contents and expiration dates.
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="bg-muted p-4 rounded-lg">
                      <h3 className="font-semibold mb-2">Tips for Effective Donations:</h3>
                      <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                        <li>Coordinate with receiving organizations to understand their needs</li>
                        <li>Consider donating a variety of food groups for balanced nutrition</li>
                        <li>Be mindful of cultural preferences and dietary restrictions</li>
                        <li>Donate non-perishable items with longer shelf lives when possible</li>
                      </ul>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
              <TabsContent value="faq">
                <Card>
                  <CardHeader>
                    <CardTitle>Frequently Asked Questions</CardTitle>
                    <CardDescription>
                      Find answers to common questions about food donation and our platform.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Accordion type="single" collapsible className="w-full">
                      <AccordionItem value="item-1">
                        <AccordionTrigger>What types of food can I donate?</AccordionTrigger>
                        <AccordionContent>
                          You can donate a wide variety of foods, including non-perishable items, fresh produce, baked goods,
                          and prepared meals. The key is to ensure that all donated food is safe for consumption and properly
                          packaged. Avoid donating food that is past its expiration date or has been previously served.
                        </AccordionContent>
                      </AccordionItem>
                      <AccordionItem value="item-2">
                        <AccordionTrigger>How do I ensure my donation reaches those in need?</AccordionTrigger>
                        <AccordionContent>
                          Our platform connects donors directly with verified receiving organizations. When you list a
                          donation, nearby receivers will be notified based on their needs and capacity. You can also choose
                          to deliver the donation yourself or opt for our volunteer network to assist with transportation.
                        </AccordionContent>
                      </AccordionItem>
                      <AccordionItem value="item-3">
                        <AccordionTrigger>Are there any tax benefits for donating food?</AccordionTrigger>
                        <AccordionContent>
                          In many cases, food donations can be tax-deductible. However, tax laws vary by country and region.
                          We recommend consulting with a tax professional or referring to your local tax authority's guidelines
                          for specific information on potential tax benefits related to food donations.
                        </AccordionContent>
                      </AccordionItem>
                      <AccordionItem value="item-4">
                        <AccordionTrigger>How can I become a volunteer?</AccordionTrigger>
                        <AccordionContent>
                          To become a volunteer, simply update your profile settings and opt-in to volunteer opportunities.
                          You'll then be notified of nearby donation requests that need assistance with transportation or
                          distribution. You can choose which opportunities to accept based on your availability and preferences.
                        </AccordionContent>
                      </AccordionItem>
                      <AccordionItem value="item-5">
                        <AccordionTrigger>What safety measures are in place for food handling?</AccordionTrigger>
                        <AccordionContent>
                          We provide comprehensive food safety guidelines for all users of our platform. Donors are required to
                          follow these guidelines when preparing and packaging food for donation. Receiving organizations are
                          also trained in proper food handling and storage practices. Additionally, our volunteer network
                          receives basic food safety training to ensure proper handling during transportation.
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>
        </section>
      </main>
      <footer className="flex flex-col gap-2 sm:flex-row py-6 w-full shrink-0 items-center px-4 md:px-6 border-t">
        <p className="text-xs text-gray-500 dark:text-gray-400">© 2024 FoodShare. All rights reserved.</p>
        <nav className="sm:ml-auto flex gap-4 sm:gap-6">
          <Link className="text-xs hover:underline underline-offset-4" href="#">
            Terms of Service
          </Link>
          <Link className="text-xs hover:underline underline-offset-4" href="#">
            Privacy
          </Link>
        </nav>
      </footer>
    </div>
  )
}