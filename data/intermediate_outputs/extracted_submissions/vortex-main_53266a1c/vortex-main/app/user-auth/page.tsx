"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Utensils } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { auth } from "@/lib/firebase";
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
} from "firebase/auth";
import "@/app/globals.css";

export default function UserAuthComponent() {
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab") || "login";
  const router = useRouter();
  const [activeTab, setActiveTab] = useState(initialTab);
  const [userType, setUserType] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState(""); // For registration
  const [loading, setLoading] = useState(false);

  const handleLoginSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      await signInWithEmailAndPassword(auth, email, password);
      if (userType === "donor") {
        router.push("/donor-page");
      } else if (userType === "receiver") {
        router.push("/receiver-page");
      }
    } catch (error) {
      console.error("Login error:", error);
      // Handle error (e.g., show a notification)
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      const userCredential = await createUserWithEmailAndPassword(
        auth,
        email,
        password
      );
      // You might want to call your backend API to save user info and role
      console.log("Registration successful:", userCredential.user);
      setActiveTab("login");
      router.push("?tab=login");
    } catch (error) {
      console.error("Registration error:", error);
      // Handle error (e.g., show a notification)
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setActiveTab(initialTab);
  }, [initialTab]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-2">
            <Utensils className="h-6 w-6 mr-2" />
            <CardTitle className="text-2xl font-bold">FoodShare</CardTitle>
          </div>
          <CardDescription>
            {activeTab === "login"
              ? "Sign in to your account"
              : "Create a new account"}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">Login</TabsTrigger>
              <TabsTrigger value="register">Register</TabsTrigger>
            </TabsList>
            <TabsContent value="login">
              <form onSubmit={handleLoginSubmit}>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="m@example.com"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="userType">Select</Label>
                    <Select
                      value={userType}
                      onValueChange={setUserType}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select user type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="donor">Donor</SelectItem>
                        <SelectItem value="receiver">Receiver</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="submit"
                    className="w-full btn"
                    disabled={loading}
                  >
                    {loading ? "Signing In..." : "Sign In"}
                  </Button>
                </div>
              </form>
            </TabsContent>
            <TabsContent value="register">
              <form onSubmit={handleRegisterSubmit}>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      placeholder="John Doe"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="m@example.com"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="userType">Select</Label>
                    <Select
                      value={userType}
                      onValueChange={setUserType}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select user type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="donor">Donor</SelectItem>
                        <SelectItem value="receiver">Receiver</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button
                    type="submit"
                    className="bg-primary w-full btn"
                    disabled={loading}
                  >
                    {loading ? "Creating Account..." : "Create Account"}
                  </Button>
                </div>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
        <CardFooter>
          <div className="text-sm text-muted-foreground text-center w-full">
            {activeTab === "login" ? (
              <>
                Don't have an account?{" "}
                <Button
                  variant="link"
                  className="p-0"
                  onClick={() => setActiveTab("register")}
                >
                  Sign up
                </Button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <Button
                  variant="link"
                  className="p-0"
                  onClick={() => setActiveTab("login")}
                >
                  Sign in
                </Button>
              </>
            )}
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
