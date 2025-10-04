import express from "express";
import passport from "passport";
import User from "../models/User.js";
import Post from "../models/Post.js";
import bcrypt from "bcryptjs";
import { ensureAuthenticated } from "../middleware/auth.js"; // Import middleware to protect routes

const router = express.Router();

// @route   GET /users/login
router.get("/login", (req, res) =>
  res.render("login", { error_msg: req.flash("error_msg") })
);

// @route   POST /users/login
router.post("/login", (req, res, next) => {
  passport.authenticate("local", {
    successRedirect: "/",
    failureRedirect: "/users/login",
    failureFlash: true,
  })(req, res, next);
});

// @route   GET /users/signup
router.get("/signup", (req, res) =>
  res.render("signup", { error_msg: req.flash("error_msg") })
);

// @route   POST /users/signup
router.post("/signup", async (req, res) => {
  const { username, email, password, password2 } = req.body;
  if (password !== password2) {
    req.flash("error_msg", "Passwords do not match");
    return res.redirect("/users/signup");
  }

  try {
    let user = await User.findOne({ email });
    if (user) {
      req.flash("error_msg", "Email already registered");
      return res.redirect("/users/signup");
    } else {
      user = new User({
        username,
        email,
        password,
      });

      const salt = await bcrypt.genSalt(10);
      user.password = await bcrypt.hash(password, salt);

      await user.save();
      req.flash("success_msg", "You are now registered and can log in");
      res.redirect("/users/login");
    }
  } catch (error) {
    console.error(error);
    res.status(500).send("Server Error");
  }
});

// @route   GET /users/profile
// Profile page, protected route
router.get("/profile", ensureAuthenticated, async (req, res) => {
  try {
    const posts = await Post.find({ user: req.user.id }).sort({ date: -1 }); // Find posts by the logged-in user
    res.render("profile", { posts, user: req.user }); // Pass posts and user data to the profile view
  } catch (error) {
    console.error(error);
    res.status(500).send("Server Error");
  }
});

// @route   GET /users/logout
router.get("/logout", (req, res) => {
  req.logout(() => {
    req.flash("success_msg", "You have logged out");
    res.redirect("/users/login");
  });
});

// @route   GET /users/edit-profile
router.get("/edit-profile", ensureAuthenticated, (req, res) => {
  res.render("editProfile", { user: req.user });
});

// @route GET /users/dashboard
router.get("/dashboard", ensureAuthenticated, async (req, res) => {
  const posts = await Post.find().sort({ date: -1 }); // Fetch all posts
  res.render("dashboard", { posts, user: req.user });
});

// @route   POST /users/edit-profile
router.post("/edit-profile", ensureAuthenticated, async (req, res) => {
  const { username, email, password, password2 } = req.body;

  if (password !== password2) {
    req.flash("error_msg", "Passwords do not match");
    return res.redirect("/users/edit-profile");
  }

  try {
    let user = await User.findById(req.user.id);

    if (!user) {
      req.flash("error_msg", "User not found");
      return res.redirect("/users/edit-profile");
    }

    // Update user details
    user.username = username;
    user.email = email;

    if (password) {
      const salt = await bcrypt.genSalt(10);
      user.password = await bcrypt.hash(password, salt);
    }

    await user.save();

    req.flash("success_msg", "Profile updated successfully");
    res.redirect("/users/profile"); // Redirect to the profile page
  } catch (error) {
    console.error(error);
    req.flash("error_msg", "Something went wrong, please try again.");
    res.redirect("/users/edit-profile");
  }
});

// @route   GET /about
// @desc    About the brand
router.get("/about", (req, res) => {
  res.render("about"); // Renders the about page
});

// @route   GET /explore
// @desc    Display all posts in grid layout
router.get("/explore", ensureAuthenticated, async (req, res) => {
  try {
    const posts = await Post.find().sort({ date: -1 }); // Fetch all posts
    res.render("explore", { posts, user: req.user }); // Pass posts to the explore view
  } catch (error) {
    console.error(error);
    res.status(500).send("Server Error");
  }
});

// @route   POST /posts/:id/delete
// @desc    Delete a post
router.post("/posts/:id/delete", ensureAuthenticated, async (req, res) => {
  try {
    const post = await Post.findById(req.params.id);

    if (!post) {
      req.flash("error_msg", "Post not found");
      return res.redirect("/users/profile");
    }

    // Ensure the post belongs to the logged-in user
    if (post.user.toString() !== req.user.id) {
      req.flash("error_msg", "You are not authorized to delete this post");
      return res.redirect("/users/profile");
    }

    await post.remove();
    req.flash("success_msg", "Post deleted successfully");
    res.redirect("/users/profile");
  } catch (error) {
    console.error(error);
    req.flash("error_msg", "Something went wrong, please try again");
    res.redirect("/users/profile");
  }
});

router.get("/skills", ensureAuthenticated, async (req, res) => {
  const posts = await Post.find().sort({ date: -1 });
  res.render("skills", { user: req.user, posts });
});

// @route   GET /rewards
router.get("/rewards", ensureAuthenticated, (req, res) => {
  const rewards = "";
  res.render("rewards", { user: req.user, rewards });
});
router.get("/admin/login", (req, res) => {
  res.render("adminLogin"); // Render the login page
});

// @route   POST /admin/login
// @desc    Handle admin login
router.post("/admin/login", (req, res) => {
  const { username, password } = req.body;

  // Check credentials
  if (username === "admin" && password === "1234567890") {
    // Redirect to admin dashboard if login is successful
    return res.redirect("/users/admin/dashboard");
  } else {
    // Re-render login page with an error message if login fails
    return res
      .status(401)
      .render("adminLogin", { error: "Invalid credentials" });
  }
});

// @route   GET /admin/dashboard
// @desc    Render admin stats page
router.get("/admin/dashboard", async (req, res) => {
  // Fetch total counts and user list
  const totalUsers = await User.countDocuments();
  const totalPosts = await Post.countDocuments();
  const totalAffiliates = "Not Available";
  const users = await User.find();

  res.render("admin", {
    totalUsers,
    totalPosts,
    totalAffiliates,
    users,
  });
});

export default router;
