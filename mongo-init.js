db = db.getSiblingDB("admin");

db.createUser({
  user: "mehrnoor",
  pwd: "mehrnoor",
  roles: [
    { role: "readWrite", db: "yourdb" },
    { role: "readWrite", db: "admin" }
  ]
});
