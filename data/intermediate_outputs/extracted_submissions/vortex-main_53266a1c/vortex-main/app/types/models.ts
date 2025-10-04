// Suppress unused variable warning
/* eslint-disable @typescript-eslint/no-unused-vars */

interface IUser {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface IDonation {
  id: string;
  donorId: string;
  receiverId: string;
  foodForPeople: number;
  foodUsedFor: string;
  description: string;
  expiry: string;
  canDeliver: boolean;
  status: string;
  createdAt: string;
  updatedAt: string;
}

interface IFeedback {
  id: string;
  donationId: string;
  receiverId: string;
  experience: string;
  peopleFed: number;
  photos: string[];
  createdAt: string;
  updatedAt: string;
}

interface INotification {
  id: string;
  userId: string;
  donationId: string;
  message: string;
  read: boolean;
  createdAt: string;
  updatedAt: string;
}

interface IReceiver {
  userId: string;
  approxPeopleFed: number;
  bioData: string;
}

interface IVolunteer {
  userId: string;
  latitude: number;
  longitude: number;
  active: boolean;
}

interface IUserModel {
  create(data: Omit<IUser, "id">): Promise<IUser>;
  findById(id: string): Promise<IUser | null>;
  findAll(): Promise<IUser[]>;
  update(id: string, data: Partial<IUser>): Promise<void>;
  delete(id: string): Promise<void>;
}

interface IDonationModel {
  create(
    data: Omit<IDonation, "id" | "createdAt" | "updatedAt">
  ): Promise<IDonation>;
  findById(id: string): Promise<IDonation | null>;
  findAll(): Promise<IDonation[]>;
  update(id: string, data: Partial<IDonation>): Promise<void>;
  delete(id: string): Promise<void>;
}

interface IFeedbackModel {
  create(
    data: Omit<IFeedback, "id" | "createdAt" | "updatedAt">
  ): Promise<IFeedback>;
  findAll(): Promise<IFeedback[]>;
}

interface INotificationModel {
  create(
    data: Omit<INotification, "id" | "createdAt" | "updatedAt" | "read">
  ): Promise<INotification>;
  findAll(): Promise<INotification[]>;
}

interface IReceiverModel {
  create(userId: string, data: Omit<IReceiver, "userId">): Promise<IReceiver>;
  findByUserId(userId: string): Promise<IReceiver | null>;
}

interface IVolunteerModel {
  create(userId: string, data: Omit<IVolunteer, "userId">): Promise<IVolunteer>;
  findByUserId(userId: string): Promise<IVolunteer | null>;
}
