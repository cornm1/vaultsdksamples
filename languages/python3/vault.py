from ctypes import *
from enum import IntEnum, unique
import platform
import os

class VdkException(Exception):
    def printout(this):
        vaultError = this.args[1]
        if (vaultError == vdkError.ConnectionFailure):
            print("Could not connect to server.")
        elif (vaultError == vdkError.AuthFailure):
            print("Username or Password incorrect.")
        elif (vaultError == vdkError.OutOfSync):
            print("Your clock doesn't match the remote server clock.")
        elif (vaultError == vdkError.SecurityFailure):
            print("Could not open a secure channel to the server.")
        elif (vaultError == vdkError.ServerFailure):
            print("Unable to negotiate with server, please confirm the server address")
        elif (vaultError != vdkError.Success):
            print("Error {}: {}; please consult Vault SDK documentation".format(this.args[1],this.args[0]))

def LoadVaultSDK(SDKPath):
  global vaultSDK
  try:
      vaultSDK = CDLL(SDKPath)
  except OSError:
    print("No local Vault shared object/dll found in current working directory, trying path in VAULTSDK_HOME environment variable...")
    SDKPath = os.environ.get("VAULTSDK_HOME")
    if SDKPath==None:
        raise FileNotFoundError("Environment variable VAULTSDK_HOME not set, please refer to Vault SDK documentation")
        
    if platform.system() == 'Windows':
        SDKPath +="/lib/win_x64/vaultSDK"

    #TODO Add support for these paths:
    #elif platform.system() == "Linux":
    #    print("Platform not supported")
        
    #elif platform.system() == "Darwin":
    #    print("Platform not supported"
    else:
        print("Platform {} not supported by this sample".format(platform.system()))
        exit()
    print("Using Vault SDK shared object located at {}".format(SDKPath))
    vaultSDK = CDLL(SDKPath)

@unique
class vdkError(IntEnum):
  Success = 0 # Indicates the operation was successful

  Failure = 1 # A catch-all value that is rarely used, internally the below values are favored
  InvalidParameter = 2 # One or more parameters is not of the expected format
  InvalidConfiguration = 3 # Something in the request is not correctly configured or has conflicting settings
  InvalidLicense = 4 # The required license isn't available or has expired
  SessionExpired = 5 # The Vault Server has terminated your session

  NotAllowed = 6 # The requested operation is not allowed (usually this is because the operation isn't allowed in the current state)
  NotSupported = 7 # This functionality has not yet been implemented (usually some combination of inputs isn't compatible yet)
  NotFound = 8 # The requested item wasn't found or isn't currently available
  NotInitialized = 9 # The request can't be processed because an object hasn't been configured yet

  ConnectionFailure = 10 # There was a connection failure
  MemoryAllocationFailure = 11 # VDK wasn't able to allocate enough memory for the requested feature
  ServerFailure = 12 # The server reported an error trying to fufil the request
  AuthFailure = 13 # The provided credentials were declined (usually username or password issue)
  SecurityFailure = 14 # There was an issue somewhere in the security system- usually creating or verifying of digital signatures or cryptographic key pairs
  OutOfSync = 15 # There is an inconsistency between the internal VDK state and something external. This is usually because of a time difference between the local machine and a remote server

  ProxyError = 16 # There was some issue with the provided proxy information (either a proxy is in the way or the provided proxy info wasn't correct)
  ProxyAuthRequired = 17 # A proxy has requested authentication

  OpenFailure = 18 # A requested resource was unable to be opened
  ReadFailure = 19 # A requested resourse was unable to be read
  WriteFailure = 20 # A requested resource was unable to be written
  ParseError = 21 # A requested resource or input was unable to be parsed
  ImageParseError = 22 # An image was unable to be parsed. This is usually an indication of either a corrupt or unsupported image format

  Pending = 23 # A requested operation is pending.
  TooManyRequests = 24 # This functionality is currently being rate limited or has exhausted a shared resource. Trying again later may be successful
  Cancelled = 25 # The requested operation was cancelled (usually by the user)

  Count = 26 # Internally used to verify return values

def _HandleReturnValue(retVal):
  if retVal != vdkError.Success:
    err = vdkError(retVal)
    raise VdkException(err.name, err.value)

@unique
class vdkRenderViewMatrix(IntEnum):
  Camera = 0     # The local to world-space transform of the camera (View is implicitly set as the inverse)
  View = 1       # The view-space transform for the model (does not need to be set explicitly)
  Projection = 2 # The projection matrix (default is 60 degree LH)
  Viewport = 3   # Viewport scaling matrix (default width and height of viewport)
  Count = 4

@unique
class vdkLicenseType(IntEnum):
  Render = 0
  Convert = 1
  Count = 2

class vdkAttributeSet(Structure):
  _fields_ = [("standardContent", c_uint64),
              ("count", c_uint32),
              ("allocated", c_uint32),
              ("pDescriptors", c_void_p)
              ]

class vdkPointCloudHeader(Structure):
  _fields_ = [("scaledRange", c_double),
              ("unitMeterScale", c_double),
              ("totalLODLayers", c_uint32),
              ("convertedResolution", c_double),
              ("storedMatrix", c_double * 16),
              ("attributes", vdkAttributeSet),
              ("baseOffset", c_double * 3),
              ("pivot", c_double * 3),
              ("boundingBoxCenter", c_double * 3),
              ("boundingBoxExtents", c_double * 3)
              ]

class vdkRenderInstance(Structure):
    _fields_ = [("pPointCloud", c_void_p),
                ("matrix", c_double * 16),
                ("modelFlags", c_uint64),
                ("pFilter", c_void_p),
                ("pVoxelShader", c_void_p),
                ("pVoxelUserData", c_void_p)
                ]

class vdkContext:
  def __init__(self):
    self.vdkContext_Connect = getattr(vaultSDK, "vdkContext_Connect")
    self.vdkContext_Disconnect = getattr(vaultSDK, "vdkContext_Disconnect")
    self.vdkContext_RequestLicense = getattr(vaultSDK, "vdkContext_RequestLicense")
    self.vdkContext_CheckLicense = getattr(vaultSDK, "vdkContext_CheckLicense")
    self.context = c_void_p(0)

  def Connect(self, url, applicationName, username, password):
    _HandleReturnValue(self.vdkContext_Connect(byref(self.context), url.encode('utf8'), applicationName.encode('utf8'), username.encode('utf8'), password.encode('utf8')))

  def Disconnect(self):
    _HandleReturnValue(self.vdkContext_Disconnect(byref(self.context)))

  def RequestLicense(self, licenseType):
    _HandleReturnValue(self.vdkContext_RequestLicense(self.context, licenseType))

  def CheckLicense(self, licenseType):
    _HandleReturnValue(self.vdkContext_CheckLicense(self.context, licenseType))

class vdkRenderContext:
  def __init__(self):
    self.vdkRenderContext_Create = getattr(vaultSDK, "vdkRenderContext_Create")
    self.vdkRenderContext_Destroy = getattr(vaultSDK, "vdkRenderContext_Destroy")
    self.vdkRenderContext_Render = getattr(vaultSDK, "vdkRenderContext_Render")
    self.renderer = c_void_p(0)

  def Create(self, context):
    _HandleReturnValue(self.vdkRenderContext_Create(context.context, byref(self.renderer)))

  def Destroy(self):
    _HandleReturnValue(self.vdkRenderContext_Destroy(byref(self.renderer)))

  def Render(self, renderView, models):
    renderInstances = (vdkRenderInstance * len(models))()
    for i, model in enumerate(models):
      renderInstances[i].pPointCloud = model.model
      renderInstances[i].matrix = model.header.storedMatrix
    _HandleReturnValue(self.vdkRenderContext_Render(self.renderer, renderView.renderView, renderInstances, len(models), c_void_p(0)))

class vdkRenderView:
  def __init__(self):
    self.vdkRenderView_Create = getattr(vaultSDK, "vdkRenderView_Create")
    self.vdkRenderView_Destroy = getattr(vaultSDK, "vdkRenderView_Destroy")
    self.vdkRenderView_SetTargets = getattr(vaultSDK, "vdkRenderView_SetTargets")
    self.vdkRenderView_SetMatrix = getattr(vaultSDK, "vdkRenderView_SetMatrix")
    self.renderView = c_void_p(0)

  def Create(self, context, vaultRenderer, width, height):
    _HandleReturnValue(self.vdkRenderView_Create(context.context, byref(self.renderView), vaultRenderer.renderer, width, height))

  def Destroy(self):
    _HandleReturnValue(self.vdkRenderView_Destroy(byref(self.renderView)))

  def SetTargets(self, colorBuffer, clearColor, depthBuffer):
    _HandleReturnValue(self.vdkRenderView_SetTargets(self.renderView, byref(colorBuffer), clearColor, byref(depthBuffer)))

  def SetMatrix(self, matrixType, matrix):
    cMatrix = (c_double * 16)(*matrix)
    _HandleReturnValue(self.vdkRenderView_SetMatrix(self.renderView, matrixType, byref(cMatrix)))

class vdkPointCloud:
  def __init__(self):
    self.vdkPointCloud_Load = getattr(vaultSDK, "vdkPointCloud_Load")
    self.vdkPointCloud_Unload = getattr(vaultSDK, "vdkPointCloud_Unload")
    self.vdkPointCloud_GetMetadata = getattr(vaultSDK, "vdkPointCloud_GetMetadata")
    self.model = c_void_p(0)
    self.header = vdkPointCloudHeader()

  def Load(self, context, modelLocation):
    _HandleReturnValue(self.vdkPointCloud_Load(context.context, byref(self.model), modelLocation.encode('utf8'), byref(self.header)))

  def Unload(self):
    _HandleReturnValue(self.vdkPointCloud_Unload(byref(self.model)))

  def GetMetadata(self):
    pMetadata = c_char_p(0)
    _HandleReturnValue(self.vdkPointCloud_GetMetadata(self.model, byref(pMetadata)))
    return pMetadata.value.decode('utf8')

class vdkConvertContext:
  def __init__(self):
      self.vdkConvert_CreateContext = getattr(vaultSDK, "vdkConvert_CreateContext")
      self.vdkConvert_DestroyContext  = getattr(vaultSDK, "vdkConvert_DestroyContext")
      self.vdkConvert_SetOutputFilename = getattr(vaultSDK, "vdkConvert_SetOutputFilename")
      self.vdkConvert_AddItem = getattr(vaultSDK, "vdkConvert_AddItem")
      self.vdkConvert_DoConvert = getattr(vaultSDK, "vdkConvert_DoConvert")
      self.convertContext = c_void_p(0)

  def Create(self, context):
      _HandleReturnValue(self.vdkConvert_CreateContext(context.context, byref(self.convertContext)))
  def Destroy(self):
      _HandleReturnValue(self.vdkConvert_DestroyContext(byref(self.convertContext)))
  def Output(self, fileName):
      _HandleReturnValue(self.vdkConvert_SetOutputFilename(self.convertContext, fileName.encode('utf8')))
  def AddItem(self, modelName):
      _HandleReturnValue(self.vdkConvert_AddItem(self.convertContext, modelName.encode('utf8')))
  def DoConvert(self):
      _HandleReturnValue(self.vdkConvert_DoConvert(self.convertContext))
