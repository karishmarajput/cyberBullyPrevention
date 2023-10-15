const asyncHandler = require("express-async-handler");
const { CustomError } = require("../error/custom");
const MessageModel = require("../models/Message");
const UserModel = require("../models/User");
const ChatModel = require("../models/Chat");
const axios = require("axios")
const schedule_ = require("node-schedule")
// const chats = require("../data/data");
async function getBullyingData(link,postData)
{
    var src = axios.post(link,postData).then(function(response){
        return response.data["is_cyb"]
    })
    .catch(error => {
        console.error('Error:', error);
    });
    return src
}
const editMessage = asyncHandler(async (req, res) => {
  const { id } = req.params;
  const { content } = req.body;
  
  if (!content) {
    throw new CustomError("Invalid data", 400);
  }
  try {
    const data = await MessageModel.findByIdAndUpdate(
      id,
      {
        content: content,
      },
      { new: true }
    )
      .populate("sender", "username image")
      .populate("chat");
    res.status(200).json(data);
  } catch (err) {
    throw new CustomError("Unable to edit message", 400);
  }
});

const deleteMessage=asyncHandler(async(req,res)=>{
  const { id } = req.params;

  try {
    const data = await MessageModel.findByIdAndUpdate(
      id,
      {
        isDeleted: true,
      },
      { new: true }
    )
      .populate("sender", "username image")
      .populate("chat");
    res.status(200).json(data);
  } catch (err) {
    throw new CustomError("Unable to delete message", 400);
  }
})

const messageSender = asyncHandler(async (req, res) => {
  const { content, chatId } = req.body;
  const User = await UserModel.findById({_id : req.user._id})
  if (User.ban == true){
    throw new CustomError("Banned. Please try later",400)
  }
  if(User.hits >= 3){
    const res = await UserModel.findOneAndUpdate({_id : req.user._id},{$set : {ban : true}})
  }
  const postData = {
    "text" : content
  }
  link = "http://127.0.0.1:8000/classify"
  const data = await getBullyingData(link,postData)
  const CAG = data[0];
  const OAG = data[1];
  const NAG = data[2];
  if(CAG > NAG || OAG > NAG){
    await UserModel.findOneAndUpdate({ _id: req.user._id },{$inc : {hits : 1}})
    throw new CustomError("Abusive Content",400);
  }
  
  if (!content || !chatId) {
    //   console.log("Invalid data");
    throw new CustomError("Invalid data", 400);
  }
  var newMessage = {
    sender: req.user._id,
    content: content,
    chat: chatId,
    isDeleted: false,
  };

  try {
    var message = await MessageModel.create(newMessage);

    message = await message.populate("sender", "username image");
    message = await message.populate("chat");
    message = await UserModel.populate(message, {
      path: "chat.users",
      select: "username image gmail",
    });

    await ChatModel.findByIdAndUpdate(req.body.chatId, {
      latestMessage: message,
    });

    res.status(200).json(message);
  } catch (error) {
    throw new CustomError("Unable to store message", 400);
  }
});

const getAllMessages = asyncHandler(async (req, res) => {
  try {
    const { id } = req.params;
    let data = await MessageModel.find({ chat: id });
    if (data.length === 0) {
      res.status(200).json(data);
      return;
    }
    // console.log(data);
    data = await MessageModel.find({ chat: id })
      .populate("sender", "username image")
      .populate("chat");
    res.status(200).json(data);
  } catch (err) {
    console.log(err);
    throw new CustomError("Unable to fetch messages", 400);
  }
});
async function decrementHits(){
  try {
      const allUsers = await UserModel.find({});
      for (const user_temp of allUsers){
          if (user_temp.hits > 0)
          {
              await UserModel.updateOne(
                  { _id: user_temp._id },
                  { $inc: { hits: -1 } }
              );
          }
      }
  } catch (error) {
      console.log("Error Encountered : ",error)
  }
}
async function checkAndChangeStatus(){
  try {
      const allUsers = await UserModel.find({});
      for (const user_temp of allUsers){
          if (user_temp.hits < 3)
          {
              await UserModel.updateOne(
                  { _id: user_temp._id },
                  { $set: { ban : false } }
              );
          }
      }
  } catch (error) {
      console.error("Error encountered:",error)
  }
}
schedule_.scheduleJob('*/5 * * * *', decrementHits);
schedule_.scheduleJob("* * * * * *",checkAndChangeStatus);
module.exports = {
  messageSender,
  getAllMessages,
  editMessage,
  deleteMessage
};
