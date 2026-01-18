"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
(() => {
var exports = {};
exports.id = "app/api/auth/[...nextauth]/route";
exports.ids = ["app/api/auth/[...nextauth]/route"];
exports.modules = {

/***/ "@prisma/client":
/*!*********************************!*\
  !*** external "@prisma/client" ***!
  \*********************************/
/***/ ((module) => {

module.exports = require("@prisma/client");

/***/ }),

/***/ "../../client/components/action-async-storage.external":
/*!*******************************************************************************!*\
  !*** external "next/dist/client/components/action-async-storage.external.js" ***!
  \*******************************************************************************/
/***/ ((module) => {

module.exports = require("next/dist/client/components/action-async-storage.external.js");

/***/ }),

/***/ "../../client/components/request-async-storage.external":
/*!********************************************************************************!*\
  !*** external "next/dist/client/components/request-async-storage.external.js" ***!
  \********************************************************************************/
/***/ ((module) => {

module.exports = require("next/dist/client/components/request-async-storage.external.js");

/***/ }),

/***/ "../../client/components/static-generation-async-storage.external":
/*!******************************************************************************************!*\
  !*** external "next/dist/client/components/static-generation-async-storage.external.js" ***!
  \******************************************************************************************/
/***/ ((module) => {

module.exports = require("next/dist/client/components/static-generation-async-storage.external.js");

/***/ }),

/***/ "next/dist/compiled/next-server/app-route.runtime.dev.js":
/*!**************************************************************************!*\
  !*** external "next/dist/compiled/next-server/app-route.runtime.dev.js" ***!
  \**************************************************************************/
/***/ ((module) => {

module.exports = require("next/dist/compiled/next-server/app-route.runtime.dev.js");

/***/ }),

/***/ "assert":
/*!*************************!*\
  !*** external "assert" ***!
  \*************************/
/***/ ((module) => {

module.exports = require("assert");

/***/ }),

/***/ "buffer":
/*!*************************!*\
  !*** external "buffer" ***!
  \*************************/
/***/ ((module) => {

module.exports = require("buffer");

/***/ }),

/***/ "crypto":
/*!*************************!*\
  !*** external "crypto" ***!
  \*************************/
/***/ ((module) => {

module.exports = require("crypto");

/***/ }),

/***/ "events":
/*!*************************!*\
  !*** external "events" ***!
  \*************************/
/***/ ((module) => {

module.exports = require("events");

/***/ }),

/***/ "http":
/*!***********************!*\
  !*** external "http" ***!
  \***********************/
/***/ ((module) => {

module.exports = require("http");

/***/ }),

/***/ "https":
/*!************************!*\
  !*** external "https" ***!
  \************************/
/***/ ((module) => {

module.exports = require("https");

/***/ }),

/***/ "querystring":
/*!******************************!*\
  !*** external "querystring" ***!
  \******************************/
/***/ ((module) => {

module.exports = require("querystring");

/***/ }),

/***/ "url":
/*!**********************!*\
  !*** external "url" ***!
  \**********************/
/***/ ((module) => {

module.exports = require("url");

/***/ }),

/***/ "util":
/*!***********************!*\
  !*** external "util" ***!
  \***********************/
/***/ ((module) => {

module.exports = require("util");

/***/ }),

/***/ "zlib":
/*!***********************!*\
  !*** external "zlib" ***!
  \***********************/
/***/ ((module) => {

module.exports = require("zlib");

/***/ }),

/***/ "(rsc)/./node_modules/next/dist/build/webpack/loaders/next-app-loader.js?name=app%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute&page=%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute&appPaths=&pagePath=private-next-app-dir%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute.ts&appDir=C%3A%5CUsers%5CSeth%20R%5CDesktop%5Cpredictbot-stack%5Cmodules%5Cadmin_portal%5Csrc%5Capp&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&rootDir=C%3A%5CUsers%5CSeth%20R%5CDesktop%5Cpredictbot-stack%5Cmodules%5Cadmin_portal&isDev=true&tsconfigPath=tsconfig.json&basePath=&assetPrefix=&nextConfigOutput=standalone&preferredRegion=&middlewareConfig=e30%3D!":
/*!******************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************!*\
  !*** ./node_modules/next/dist/build/webpack/loaders/next-app-loader.js?name=app%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute&page=%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute&appPaths=&pagePath=private-next-app-dir%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute.ts&appDir=C%3A%5CUsers%5CSeth%20R%5CDesktop%5Cpredictbot-stack%5Cmodules%5Cadmin_portal%5Csrc%5Capp&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&rootDir=C%3A%5CUsers%5CSeth%20R%5CDesktop%5Cpredictbot-stack%5Cmodules%5Cadmin_portal&isDev=true&tsconfigPath=tsconfig.json&basePath=&assetPrefix=&nextConfigOutput=standalone&preferredRegion=&middlewareConfig=e30%3D! ***!
  \******************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   headerHooks: () => (/* binding */ headerHooks),\n/* harmony export */   originalPathname: () => (/* binding */ originalPathname),\n/* harmony export */   patchFetch: () => (/* binding */ patchFetch),\n/* harmony export */   requestAsyncStorage: () => (/* binding */ requestAsyncStorage),\n/* harmony export */   routeModule: () => (/* binding */ routeModule),\n/* harmony export */   serverHooks: () => (/* binding */ serverHooks),\n/* harmony export */   staticGenerationAsyncStorage: () => (/* binding */ staticGenerationAsyncStorage),\n/* harmony export */   staticGenerationBailout: () => (/* binding */ staticGenerationBailout)\n/* harmony export */ });\n/* harmony import */ var next_dist_server_future_route_modules_app_route_module_compiled__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! next/dist/server/future/route-modules/app-route/module.compiled */ \"(rsc)/./node_modules/next/dist/server/future/route-modules/app-route/module.compiled.js\");\n/* harmony import */ var next_dist_server_future_route_modules_app_route_module_compiled__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(next_dist_server_future_route_modules_app_route_module_compiled__WEBPACK_IMPORTED_MODULE_0__);\n/* harmony import */ var next_dist_server_future_route_kind__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! next/dist/server/future/route-kind */ \"(rsc)/./node_modules/next/dist/server/future/route-kind.js\");\n/* harmony import */ var next_dist_server_lib_patch_fetch__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! next/dist/server/lib/patch-fetch */ \"(rsc)/./node_modules/next/dist/server/lib/patch-fetch.js\");\n/* harmony import */ var next_dist_server_lib_patch_fetch__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(next_dist_server_lib_patch_fetch__WEBPACK_IMPORTED_MODULE_2__);\n/* harmony import */ var C_Users_Seth_R_Desktop_predictbot_stack_modules_admin_portal_src_app_api_auth_nextauth_route_ts__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! ./src/app/api/auth/[...nextauth]/route.ts */ \"(rsc)/./src/app/api/auth/[...nextauth]/route.ts\");\n\n\n\n\n// We inject the nextConfigOutput here so that we can use them in the route\n// module.\nconst nextConfigOutput = \"standalone\"\nconst routeModule = new next_dist_server_future_route_modules_app_route_module_compiled__WEBPACK_IMPORTED_MODULE_0__.AppRouteRouteModule({\n    definition: {\n        kind: next_dist_server_future_route_kind__WEBPACK_IMPORTED_MODULE_1__.RouteKind.APP_ROUTE,\n        page: \"/api/auth/[...nextauth]/route\",\n        pathname: \"/api/auth/[...nextauth]\",\n        filename: \"route\",\n        bundlePath: \"app/api/auth/[...nextauth]/route\"\n    },\n    resolvedPagePath: \"C:\\\\Users\\\\Seth R\\\\Desktop\\\\predictbot-stack\\\\modules\\\\admin_portal\\\\src\\\\app\\\\api\\\\auth\\\\[...nextauth]\\\\route.ts\",\n    nextConfigOutput,\n    userland: C_Users_Seth_R_Desktop_predictbot_stack_modules_admin_portal_src_app_api_auth_nextauth_route_ts__WEBPACK_IMPORTED_MODULE_3__\n});\n// Pull out the exports that we need to expose from the module. This should\n// be eliminated when we've moved the other routes to the new format. These\n// are used to hook into the route.\nconst { requestAsyncStorage, staticGenerationAsyncStorage, serverHooks, headerHooks, staticGenerationBailout } = routeModule;\nconst originalPathname = \"/api/auth/[...nextauth]/route\";\nfunction patchFetch() {\n    return (0,next_dist_server_lib_patch_fetch__WEBPACK_IMPORTED_MODULE_2__.patchFetch)({\n        serverHooks,\n        staticGenerationAsyncStorage\n    });\n}\n\n\n//# sourceMappingURL=app-route.js.map//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHJzYykvLi9ub2RlX21vZHVsZXMvbmV4dC9kaXN0L2J1aWxkL3dlYnBhY2svbG9hZGVycy9uZXh0LWFwcC1sb2FkZXIuanM/bmFtZT1hcHAlMkZhcGklMkZhdXRoJTJGJTVCLi4ubmV4dGF1dGglNUQlMkZyb3V0ZSZwYWdlPSUyRmFwaSUyRmF1dGglMkYlNUIuLi5uZXh0YXV0aCU1RCUyRnJvdXRlJmFwcFBhdGhzPSZwYWdlUGF0aD1wcml2YXRlLW5leHQtYXBwLWRpciUyRmFwaSUyRmF1dGglMkYlNUIuLi5uZXh0YXV0aCU1RCUyRnJvdXRlLnRzJmFwcERpcj1DJTNBJTVDVXNlcnMlNUNTZXRoJTIwUiU1Q0Rlc2t0b3AlNUNwcmVkaWN0Ym90LXN0YWNrJTVDbW9kdWxlcyU1Q2FkbWluX3BvcnRhbCU1Q3NyYyU1Q2FwcCZwYWdlRXh0ZW5zaW9ucz10c3gmcGFnZUV4dGVuc2lvbnM9dHMmcGFnZUV4dGVuc2lvbnM9anN4JnBhZ2VFeHRlbnNpb25zPWpzJnJvb3REaXI9QyUzQSU1Q1VzZXJzJTVDU2V0aCUyMFIlNUNEZXNrdG9wJTVDcHJlZGljdGJvdC1zdGFjayU1Q21vZHVsZXMlNUNhZG1pbl9wb3J0YWwmaXNEZXY9dHJ1ZSZ0c2NvbmZpZ1BhdGg9dHNjb25maWcuanNvbiZiYXNlUGF0aD0mYXNzZXRQcmVmaXg9Jm5leHRDb25maWdPdXRwdXQ9c3RhbmRhbG9uZSZwcmVmZXJyZWRSZWdpb249Jm1pZGRsZXdhcmVDb25maWc9ZTMwJTNEISIsIm1hcHBpbmdzIjoiOzs7Ozs7Ozs7Ozs7Ozs7OztBQUFzRztBQUN2QztBQUNjO0FBQ2lFO0FBQzlJO0FBQ0E7QUFDQTtBQUNBLHdCQUF3QixnSEFBbUI7QUFDM0M7QUFDQSxjQUFjLHlFQUFTO0FBQ3ZCO0FBQ0E7QUFDQTtBQUNBO0FBQ0EsS0FBSztBQUNMO0FBQ0E7QUFDQSxZQUFZO0FBQ1osQ0FBQztBQUNEO0FBQ0E7QUFDQTtBQUNBLFFBQVEsdUdBQXVHO0FBQy9HO0FBQ0E7QUFDQSxXQUFXLDRFQUFXO0FBQ3RCO0FBQ0E7QUFDQSxLQUFLO0FBQ0w7QUFDNko7O0FBRTdKIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vcHJlZGljdGJvdC1hZG1pbi8/ZjAzYSJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgeyBBcHBSb3V0ZVJvdXRlTW9kdWxlIH0gZnJvbSBcIm5leHQvZGlzdC9zZXJ2ZXIvZnV0dXJlL3JvdXRlLW1vZHVsZXMvYXBwLXJvdXRlL21vZHVsZS5jb21waWxlZFwiO1xuaW1wb3J0IHsgUm91dGVLaW5kIH0gZnJvbSBcIm5leHQvZGlzdC9zZXJ2ZXIvZnV0dXJlL3JvdXRlLWtpbmRcIjtcbmltcG9ydCB7IHBhdGNoRmV0Y2ggYXMgX3BhdGNoRmV0Y2ggfSBmcm9tIFwibmV4dC9kaXN0L3NlcnZlci9saWIvcGF0Y2gtZmV0Y2hcIjtcbmltcG9ydCAqIGFzIHVzZXJsYW5kIGZyb20gXCJDOlxcXFxVc2Vyc1xcXFxTZXRoIFJcXFxcRGVza3RvcFxcXFxwcmVkaWN0Ym90LXN0YWNrXFxcXG1vZHVsZXNcXFxcYWRtaW5fcG9ydGFsXFxcXHNyY1xcXFxhcHBcXFxcYXBpXFxcXGF1dGhcXFxcWy4uLm5leHRhdXRoXVxcXFxyb3V0ZS50c1wiO1xuLy8gV2UgaW5qZWN0IHRoZSBuZXh0Q29uZmlnT3V0cHV0IGhlcmUgc28gdGhhdCB3ZSBjYW4gdXNlIHRoZW0gaW4gdGhlIHJvdXRlXG4vLyBtb2R1bGUuXG5jb25zdCBuZXh0Q29uZmlnT3V0cHV0ID0gXCJzdGFuZGFsb25lXCJcbmNvbnN0IHJvdXRlTW9kdWxlID0gbmV3IEFwcFJvdXRlUm91dGVNb2R1bGUoe1xuICAgIGRlZmluaXRpb246IHtcbiAgICAgICAga2luZDogUm91dGVLaW5kLkFQUF9ST1VURSxcbiAgICAgICAgcGFnZTogXCIvYXBpL2F1dGgvWy4uLm5leHRhdXRoXS9yb3V0ZVwiLFxuICAgICAgICBwYXRobmFtZTogXCIvYXBpL2F1dGgvWy4uLm5leHRhdXRoXVwiLFxuICAgICAgICBmaWxlbmFtZTogXCJyb3V0ZVwiLFxuICAgICAgICBidW5kbGVQYXRoOiBcImFwcC9hcGkvYXV0aC9bLi4ubmV4dGF1dGhdL3JvdXRlXCJcbiAgICB9LFxuICAgIHJlc29sdmVkUGFnZVBhdGg6IFwiQzpcXFxcVXNlcnNcXFxcU2V0aCBSXFxcXERlc2t0b3BcXFxccHJlZGljdGJvdC1zdGFja1xcXFxtb2R1bGVzXFxcXGFkbWluX3BvcnRhbFxcXFxzcmNcXFxcYXBwXFxcXGFwaVxcXFxhdXRoXFxcXFsuLi5uZXh0YXV0aF1cXFxccm91dGUudHNcIixcbiAgICBuZXh0Q29uZmlnT3V0cHV0LFxuICAgIHVzZXJsYW5kXG59KTtcbi8vIFB1bGwgb3V0IHRoZSBleHBvcnRzIHRoYXQgd2UgbmVlZCB0byBleHBvc2UgZnJvbSB0aGUgbW9kdWxlLiBUaGlzIHNob3VsZFxuLy8gYmUgZWxpbWluYXRlZCB3aGVuIHdlJ3ZlIG1vdmVkIHRoZSBvdGhlciByb3V0ZXMgdG8gdGhlIG5ldyBmb3JtYXQuIFRoZXNlXG4vLyBhcmUgdXNlZCB0byBob29rIGludG8gdGhlIHJvdXRlLlxuY29uc3QgeyByZXF1ZXN0QXN5bmNTdG9yYWdlLCBzdGF0aWNHZW5lcmF0aW9uQXN5bmNTdG9yYWdlLCBzZXJ2ZXJIb29rcywgaGVhZGVySG9va3MsIHN0YXRpY0dlbmVyYXRpb25CYWlsb3V0IH0gPSByb3V0ZU1vZHVsZTtcbmNvbnN0IG9yaWdpbmFsUGF0aG5hbWUgPSBcIi9hcGkvYXV0aC9bLi4ubmV4dGF1dGhdL3JvdXRlXCI7XG5mdW5jdGlvbiBwYXRjaEZldGNoKCkge1xuICAgIHJldHVybiBfcGF0Y2hGZXRjaCh7XG4gICAgICAgIHNlcnZlckhvb2tzLFxuICAgICAgICBzdGF0aWNHZW5lcmF0aW9uQXN5bmNTdG9yYWdlXG4gICAgfSk7XG59XG5leHBvcnQgeyByb3V0ZU1vZHVsZSwgcmVxdWVzdEFzeW5jU3RvcmFnZSwgc3RhdGljR2VuZXJhdGlvbkFzeW5jU3RvcmFnZSwgc2VydmVySG9va3MsIGhlYWRlckhvb2tzLCBzdGF0aWNHZW5lcmF0aW9uQmFpbG91dCwgb3JpZ2luYWxQYXRobmFtZSwgcGF0Y2hGZXRjaCwgIH07XG5cbi8vIyBzb3VyY2VNYXBwaW5nVVJMPWFwcC1yb3V0ZS5qcy5tYXAiXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///(rsc)/./node_modules/next/dist/build/webpack/loaders/next-app-loader.js?name=app%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute&page=%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute&appPaths=&pagePath=private-next-app-dir%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute.ts&appDir=C%3A%5CUsers%5CSeth%20R%5CDesktop%5Cpredictbot-stack%5Cmodules%5Cadmin_portal%5Csrc%5Capp&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&rootDir=C%3A%5CUsers%5CSeth%20R%5CDesktop%5Cpredictbot-stack%5Cmodules%5Cadmin_portal&isDev=true&tsconfigPath=tsconfig.json&basePath=&assetPrefix=&nextConfigOutput=standalone&preferredRegion=&middlewareConfig=e30%3D!\n");

/***/ }),

/***/ "(rsc)/./src/app/api/auth/[...nextauth]/route.ts":
/*!*************************************************!*\
  !*** ./src/app/api/auth/[...nextauth]/route.ts ***!
  \*************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   GET: () => (/* binding */ handler),\n/* harmony export */   POST: () => (/* binding */ handler)\n/* harmony export */ });\n/* harmony import */ var next_auth__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! next-auth */ \"(rsc)/./node_modules/next-auth/index.js\");\n/* harmony import */ var next_auth__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(next_auth__WEBPACK_IMPORTED_MODULE_0__);\n/* harmony import */ var _lib_auth__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! @/lib/auth */ \"(rsc)/./src/lib/auth.ts\");\n\n\nconst handler = next_auth__WEBPACK_IMPORTED_MODULE_0___default()(_lib_auth__WEBPACK_IMPORTED_MODULE_1__.authOptions);\n\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHJzYykvLi9zcmMvYXBwL2FwaS9hdXRoL1suLi5uZXh0YXV0aF0vcm91dGUudHMiLCJtYXBwaW5ncyI6Ijs7Ozs7Ozs7QUFBaUM7QUFDUTtBQUV6QyxNQUFNRSxVQUFVRixnREFBUUEsQ0FBQ0Msa0RBQVdBO0FBRU8iLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9wcmVkaWN0Ym90LWFkbWluLy4vc3JjL2FwcC9hcGkvYXV0aC9bLi4ubmV4dGF1dGhdL3JvdXRlLnRzPzAwOTgiXSwic291cmNlc0NvbnRlbnQiOlsiaW1wb3J0IE5leHRBdXRoIGZyb20gJ25leHQtYXV0aCc7XHJcbmltcG9ydCB7IGF1dGhPcHRpb25zIH0gZnJvbSAnQC9saWIvYXV0aCc7XHJcblxyXG5jb25zdCBoYW5kbGVyID0gTmV4dEF1dGgoYXV0aE9wdGlvbnMpO1xyXG5cclxuZXhwb3J0IHsgaGFuZGxlciBhcyBHRVQsIGhhbmRsZXIgYXMgUE9TVCB9O1xyXG4iXSwibmFtZXMiOlsiTmV4dEF1dGgiLCJhdXRoT3B0aW9ucyIsImhhbmRsZXIiLCJHRVQiLCJQT1NUIl0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(rsc)/./src/app/api/auth/[...nextauth]/route.ts\n");

/***/ }),

/***/ "(rsc)/./src/lib/auth.ts":
/*!*************************!*\
  !*** ./src/lib/auth.ts ***!
  \*************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   authOptions: () => (/* binding */ authOptions),\n/* harmony export */   canEditConfig: () => (/* binding */ canEditConfig),\n/* harmony export */   canManagePositions: () => (/* binding */ canManagePositions),\n/* harmony export */   canManageStrategies: () => (/* binding */ canManageStrategies),\n/* harmony export */   canManageUsers: () => (/* binding */ canManageUsers),\n/* harmony export */   canUseEmergencyControls: () => (/* binding */ canUseEmergencyControls),\n/* harmony export */   canViewAuditLogs: () => (/* binding */ canViewAuditLogs),\n/* harmony export */   \"default\": () => (__WEBPACK_DEFAULT_EXPORT__),\n/* harmony export */   hashPassword: () => (/* binding */ hashPassword),\n/* harmony export */   logAuditAction: () => (/* binding */ logAuditAction)\n/* harmony export */ });\n/* harmony import */ var next_auth_providers_credentials__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! next-auth/providers/credentials */ \"(rsc)/./node_modules/next-auth/providers/credentials.js\");\n/* harmony import */ var _prisma__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./prisma */ \"(rsc)/./src/lib/prisma.ts\");\n/* harmony import */ var bcryptjs__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! bcryptjs */ \"(rsc)/./node_modules/bcryptjs/index.js\");\n/* harmony import */ var bcryptjs__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(bcryptjs__WEBPACK_IMPORTED_MODULE_2__);\n\n\n\nconst authOptions = {\n    providers: [\n        (0,next_auth_providers_credentials__WEBPACK_IMPORTED_MODULE_0__[\"default\"])({\n            name: \"Credentials\",\n            credentials: {\n                username: {\n                    label: \"Username\",\n                    type: \"text\"\n                },\n                password: {\n                    label: \"Password\",\n                    type: \"password\"\n                }\n            },\n            async authorize (credentials) {\n                if (!credentials?.username || !credentials?.password) {\n                    throw new Error(\"Username and password are required\");\n                }\n                // Check for environment-based admin user first\n                const envUsername = process.env.ADMIN_USERNAME;\n                const envPassword = process.env.ADMIN_PASSWORD;\n                if (envUsername && envPassword && credentials.username === envUsername && credentials.password === envPassword) {\n                    return {\n                        id: \"env-admin\",\n                        username: envUsername,\n                        role: \"ADMIN\"\n                    };\n                }\n                // Check database for user\n                try {\n                    const user = await _prisma__WEBPACK_IMPORTED_MODULE_1__.prisma.user.findUnique({\n                        where: {\n                            username: credentials.username\n                        }\n                    });\n                    if (!user) {\n                        throw new Error(\"Invalid username or password\");\n                    }\n                    const isValidPassword = await (0,bcryptjs__WEBPACK_IMPORTED_MODULE_2__.compare)(credentials.password, user.passwordHash);\n                    if (!isValidPassword) {\n                        throw new Error(\"Invalid username or password\");\n                    }\n                    // Update last login\n                    await _prisma__WEBPACK_IMPORTED_MODULE_1__.prisma.user.update({\n                        where: {\n                            id: user.id\n                        },\n                        data: {\n                            lastLogin: new Date()\n                        }\n                    });\n                    return {\n                        id: user.id,\n                        username: user.username,\n                        role: user.role\n                    };\n                } catch (error) {\n                    // If database is not available, only allow env-based auth\n                    console.error(\"Database auth error:\", error);\n                    throw new Error(\"Authentication failed\");\n                }\n            }\n        })\n    ],\n    callbacks: {\n        async jwt ({ token, user }) {\n            if (user) {\n                token.id = user.id;\n                token.username = user.username;\n                token.role = user.role;\n            }\n            return token;\n        },\n        async session ({ session, token }) {\n            session.user = {\n                id: token.id,\n                username: token.username,\n                role: token.role\n            };\n            return session;\n        }\n    },\n    pages: {\n        signIn: \"/login\",\n        error: \"/login\"\n    },\n    session: {\n        strategy: \"jwt\",\n        maxAge: 24 * 60 * 60\n    },\n    secret: process.env.NEXTAUTH_SECRET\n};\n// Role-based access control helpers\nfunction canManageStrategies(role) {\n    return role === \"ADMIN\" || role === \"OPERATOR\";\n}\nfunction canManagePositions(role) {\n    return role === \"ADMIN\" || role === \"OPERATOR\";\n}\nfunction canEditConfig(role) {\n    return role === \"ADMIN\";\n}\nfunction canUseEmergencyControls(role) {\n    return role === \"ADMIN\" || role === \"OPERATOR\";\n}\nfunction canViewAuditLogs(role) {\n    return role === \"ADMIN\";\n}\nfunction canManageUsers(role) {\n    return role === \"ADMIN\";\n}\n// Utility to hash passwords\nasync function hashPassword(password) {\n    return (0,bcryptjs__WEBPACK_IMPORTED_MODULE_2__.hash)(password, 12);\n}\n// Audit logging helper\nasync function logAuditAction(userId, action, resource, details, request) {\n    try {\n        await _prisma__WEBPACK_IMPORTED_MODULE_1__.prisma.auditLog.create({\n            data: {\n                userId,\n                action,\n                resource,\n                details: details || {},\n                ipAddress: request?.ip,\n                userAgent: request?.userAgent\n            }\n        });\n    } catch (error) {\n        console.error(\"Failed to create audit log:\", error);\n    }\n}\n/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (authOptions);\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,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LFdBQVdBLFNBQVM7QUFDdEM7QUFFTyxTQUFTdUIsbUJBQW1CdkIsSUFBVTtJQUMzQyxPQUFPQSxTQUFTLFdBQVdBLFNBQVM7QUFDdEM7QUFFTyxTQUFTd0IsY0FBY3hCLElBQVU7SUFDdEMsT0FBT0EsU0FBUztBQUNsQjtBQUVPLFNBQVN5Qix3QkFBd0J6QixJQUFVO0lBQ2hELE9BQU9BLFNBQVMsV0FBV0EsU0FBUztBQUN0QztBQUVPLFNBQVMwQixpQkFBaUIxQixJQUFVO0lBQ3pDLE9BQU9BLFNBQVM7QUFDbEI7QUFFTyxTQUFTMkIsZUFBZTNCLElBQVU7SUFDdkMsT0FBT0EsU0FBUztBQUNsQjtBQUVBLDRCQUE0QjtBQUNyQixlQUFlNEIsYUFBYXRDLFFBQWdCO0lBQ2pELE9BQU9SLDhDQUFJQSxDQUFDUSxVQUFVO0FBQ3hCO0FBRUEsdUJBQXVCO0FBQ2hCLGVBQWV1QyxlQUNwQkMsTUFBYyxFQUNkQyxNQUFjLEVBQ2RDLFFBQWdCLEVBQ2hCQyxPQUFpQyxFQUNqQ0MsT0FBNkM7SUFFN0MsSUFBSTtRQUNGLE1BQU10RCwyQ0FBTUEsQ0FBQ3VELFFBQVEsQ0FBQ0MsTUFBTSxDQUFDO1lBQzNCN0IsTUFBTTtnQkFDSnVCO2dCQUNBQztnQkFDQUM7Z0JBQ0FDLFNBQVNBLFdBQVcsQ0FBQztnQkFDckJJLFdBQVdILFNBQVNJO2dCQUNwQkMsV0FBV0wsU0FBU0s7WUFDdEI7UUFDRjtJQUNGLEVBQUUsT0FBTzdCLE9BQU87UUFDZEMsUUFBUUQsS0FBSyxDQUFDLCtCQUErQkE7SUFDL0M7QUFDRjtBQUVBLGlFQUFlM0IsV0FBV0EsRUFBQyIsInNvdXJjZXMiOlsid2VicGFjazovL3ByZWRpY3Rib3QtYWRtaW4vLi9zcmMvbGliL2F1dGgudHM/NjY5MiJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgeyBOZXh0QXV0aE9wdGlvbnMgfSBmcm9tICduZXh0LWF1dGgnO1xyXG5pbXBvcnQgQ3JlZGVudGlhbHNQcm92aWRlciBmcm9tICduZXh0LWF1dGgvcHJvdmlkZXJzL2NyZWRlbnRpYWxzJztcclxuaW1wb3J0IHsgcHJpc21hIH0gZnJvbSAnLi9wcmlzbWEnO1xyXG5pbXBvcnQgeyBjb21wYXJlLCBoYXNoIH0gZnJvbSAnYmNyeXB0anMnO1xyXG5pbXBvcnQgdHlwZSB7IFJvbGUgfSBmcm9tICdAL3R5cGVzJztcclxuXHJcbi8vIEV4dGVuZCB0aGUgYnVpbHQtaW4gc2Vzc2lvbiB0eXBlc1xyXG5kZWNsYXJlIG1vZHVsZSAnbmV4dC1hdXRoJyB7XHJcbiAgaW50ZXJmYWNlIFNlc3Npb24ge1xyXG4gICAgdXNlcjoge1xyXG4gICAgICBpZDogc3RyaW5nO1xyXG4gICAgICB1c2VybmFtZTogc3RyaW5nO1xyXG4gICAgICByb2xlOiBSb2xlO1xyXG4gICAgfTtcclxuICB9XHJcblxyXG4gIGludGVyZmFjZSBVc2VyIHtcclxuICAgIGlkOiBzdHJpbmc7XHJcbiAgICB1c2VybmFtZTogc3RyaW5nO1xyXG4gICAgcm9sZTogUm9sZTtcclxuICB9XHJcbn1cclxuXHJcbmRlY2xhcmUgbW9kdWxlICduZXh0LWF1dGgvand0JyB7XHJcbiAgaW50ZXJmYWNlIEpXVCB7XHJcbiAgICBpZDogc3RyaW5nO1xyXG4gICAgdXNlcm5hbWU6IHN0cmluZztcclxuICAgIHJvbGU6IFJvbGU7XHJcbiAgfVxyXG59XHJcblxyXG5leHBvcnQgY29uc3QgYXV0aE9wdGlvbnM6IE5leHRBdXRoT3B0aW9ucyA9IHtcclxuICBwcm92aWRlcnM6IFtcclxuICAgIENyZWRlbnRpYWxzUHJvdmlkZXIoe1xyXG4gICAgICBuYW1lOiAnQ3JlZGVudGlhbHMnLFxyXG4gICAgICBjcmVkZW50aWFsczoge1xyXG4gICAgICAgIHVzZXJuYW1lOiB7IGxhYmVsOiAnVXNlcm5hbWUnLCB0eXBlOiAndGV4dCcgfSxcclxuICAgICAgICBwYXNzd29yZDogeyBsYWJlbDogJ1Bhc3N3b3JkJywgdHlwZTogJ3Bhc3N3b3JkJyB9LFxyXG4gICAgICB9LFxyXG4gICAgICBhc3luYyBhdXRob3JpemUoY3JlZGVudGlhbHMpIHtcclxuICAgICAgICBpZiAoIWNyZWRlbnRpYWxzPy51c2VybmFtZSB8fCAhY3JlZGVudGlhbHM/LnBhc3N3b3JkKSB7XHJcbiAgICAgICAgICB0aHJvdyBuZXcgRXJyb3IoJ1VzZXJuYW1lIGFuZCBwYXNzd29yZCBhcmUgcmVxdWlyZWQnKTtcclxuICAgICAgICB9XHJcblxyXG4gICAgICAgIC8vIENoZWNrIGZvciBlbnZpcm9ubWVudC1iYXNlZCBhZG1pbiB1c2VyIGZpcnN0XHJcbiAgICAgICAgY29uc3QgZW52VXNlcm5hbWUgPSBwcm9jZXNzLmVudi5BRE1JTl9VU0VSTkFNRTtcclxuICAgICAgICBjb25zdCBlbnZQYXNzd29yZCA9IHByb2Nlc3MuZW52LkFETUlOX1BBU1NXT1JEO1xyXG5cclxuICAgICAgICBpZiAoXHJcbiAgICAgICAgICBlbnZVc2VybmFtZSAmJlxyXG4gICAgICAgICAgZW52UGFzc3dvcmQgJiZcclxuICAgICAgICAgIGNyZWRlbnRpYWxzLnVzZXJuYW1lID09PSBlbnZVc2VybmFtZSAmJlxyXG4gICAgICAgICAgY3JlZGVudGlhbHMucGFzc3dvcmQgPT09IGVudlBhc3N3b3JkXHJcbiAgICAgICAgKSB7XHJcbiAgICAgICAgICByZXR1cm4ge1xyXG4gICAgICAgICAgICBpZDogJ2Vudi1hZG1pbicsXHJcbiAgICAgICAgICAgIHVzZXJuYW1lOiBlbnZVc2VybmFtZSxcclxuICAgICAgICAgICAgcm9sZTogJ0FETUlOJyBhcyBSb2xlLFxyXG4gICAgICAgICAgfTtcclxuICAgICAgICB9XHJcblxyXG4gICAgICAgIC8vIENoZWNrIGRhdGFiYXNlIGZvciB1c2VyXHJcbiAgICAgICAgdHJ5IHtcclxuICAgICAgICAgIGNvbnN0IHVzZXIgPSBhd2FpdCBwcmlzbWEudXNlci5maW5kVW5pcXVlKHtcclxuICAgICAgICAgICAgd2hlcmU6IHsgdXNlcm5hbWU6IGNyZWRlbnRpYWxzLnVzZXJuYW1lIH0sXHJcbiAgICAgICAgICB9KTtcclxuXHJcbiAgICAgICAgICBpZiAoIXVzZXIpIHtcclxuICAgICAgICAgICAgdGhyb3cgbmV3IEVycm9yKCdJbnZhbGlkIHVzZXJuYW1lIG9yIHBhc3N3b3JkJyk7XHJcbiAgICAgICAgICB9XHJcblxyXG4gICAgICAgICAgY29uc3QgaXNWYWxpZFBhc3N3b3JkID0gYXdhaXQgY29tcGFyZShjcmVkZW50aWFscy5wYXNzd29yZCwgdXNlci5wYXNzd29yZEhhc2gpO1xyXG5cclxuICAgICAgICAgIGlmICghaXNWYWxpZFBhc3N3b3JkKSB7XHJcbiAgICAgICAgICAgIHRocm93IG5ldyBFcnJvcignSW52YWxpZCB1c2VybmFtZSBvciBwYXNzd29yZCcpO1xyXG4gICAgICAgICAgfVxyXG5cclxuICAgICAgICAgIC8vIFVwZGF0ZSBsYXN0IGxvZ2luXHJcbiAgICAgICAgICBhd2FpdCBwcmlzbWEudXNlci51cGRhdGUoe1xyXG4gICAgICAgICAgICB3aGVyZTogeyBpZDogdXNlci5pZCB9LFxyXG4gICAgICAgICAgICBkYXRhOiB7IGxhc3RMb2dpbjogbmV3IERhdGUoKSB9LFxyXG4gICAgICAgICAgfSk7XHJcblxyXG4gICAgICAgICAgcmV0dXJuIHtcclxuICAgICAgICAgICAgaWQ6IHVzZXIuaWQsXHJcbiAgICAgICAgICAgIHVzZXJuYW1lOiB1c2VyLnVzZXJuYW1lLFxyXG4gICAgICAgICAgICByb2xlOiB1c2VyLnJvbGUgYXMgUm9sZSxcclxuICAgICAgICAgIH07XHJcbiAgICAgICAgfSBjYXRjaCAoZXJyb3IpIHtcclxuICAgICAgICAgIC8vIElmIGRhdGFiYXNlIGlzIG5vdCBhdmFpbGFibGUsIG9ubHkgYWxsb3cgZW52LWJhc2VkIGF1dGhcclxuICAgICAgICAgIGNvbnNvbGUuZXJyb3IoJ0RhdGFiYXNlIGF1dGggZXJyb3I6JywgZXJyb3IpO1xyXG4gICAgICAgICAgdGhyb3cgbmV3IEVycm9yKCdBdXRoZW50aWNhdGlvbiBmYWlsZWQnKTtcclxuICAgICAgICB9XHJcbiAgICAgIH0sXHJcbiAgICB9KSxcclxuICBdLFxyXG4gIGNhbGxiYWNrczoge1xyXG4gICAgYXN5bmMgand0KHsgdG9rZW4sIHVzZXIgfSkge1xyXG4gICAgICBpZiAodXNlcikge1xyXG4gICAgICAgIHRva2VuLmlkID0gdXNlci5pZDtcclxuICAgICAgICB0b2tlbi51c2VybmFtZSA9IHVzZXIudXNlcm5hbWU7XHJcbiAgICAgICAgdG9rZW4ucm9sZSA9IHVzZXIucm9sZTtcclxuICAgICAgfVxyXG4gICAgICByZXR1cm4gdG9rZW47XHJcbiAgICB9LFxyXG4gICAgYXN5bmMgc2Vzc2lvbih7IHNlc3Npb24sIHRva2VuIH0pIHtcclxuICAgICAgc2Vzc2lvbi51c2VyID0ge1xyXG4gICAgICAgIGlkOiB0b2tlbi5pZCxcclxuICAgICAgICB1c2VybmFtZTogdG9rZW4udXNlcm5hbWUsXHJcbiAgICAgICAgcm9sZTogdG9rZW4ucm9sZSxcclxuICAgICAgfTtcclxuICAgICAgcmV0dXJuIHNlc3Npb247XHJcbiAgICB9LFxyXG4gIH0sXHJcbiAgcGFnZXM6IHtcclxuICAgIHNpZ25JbjogJy9sb2dpbicsXHJcbiAgICBlcnJvcjogJy9sb2dpbicsXHJcbiAgfSxcclxuICBzZXNzaW9uOiB7XHJcbiAgICBzdHJhdGVneTogJ2p3dCcsXHJcbiAgICBtYXhBZ2U6IDI0ICogNjAgKiA2MCwgLy8gMjQgaG91cnNcclxuICB9LFxyXG4gIHNlY3JldDogcHJvY2Vzcy5lbnYuTkVYVEFVVEhfU0VDUkVULFxyXG59O1xyXG5cclxuLy8gUm9sZS1iYXNlZCBhY2Nlc3MgY29udHJvbCBoZWxwZXJzXHJcbmV4cG9ydCBmdW5jdGlvbiBjYW5NYW5hZ2VTdHJhdGVnaWVzKHJvbGU6IFJvbGUpOiBib29sZWFuIHtcclxuICByZXR1cm4gcm9sZSA9PT0gJ0FETUlOJyB8fCByb2xlID09PSAnT1BFUkFUT1InO1xyXG59XHJcblxyXG5leHBvcnQgZnVuY3Rpb24gY2FuTWFuYWdlUG9zaXRpb25zKHJvbGU6IFJvbGUpOiBib29sZWFuIHtcclxuICByZXR1cm4gcm9sZSA9PT0gJ0FETUlOJyB8fCByb2xlID09PSAnT1BFUkFUT1InO1xyXG59XHJcblxyXG5leHBvcnQgZnVuY3Rpb24gY2FuRWRpdENvbmZpZyhyb2xlOiBSb2xlKTogYm9vbGVhbiB7XHJcbiAgcmV0dXJuIHJvbGUgPT09ICdBRE1JTic7XHJcbn1cclxuXHJcbmV4cG9ydCBmdW5jdGlvbiBjYW5Vc2VFbWVyZ2VuY3lDb250cm9scyhyb2xlOiBSb2xlKTogYm9vbGVhbiB7XHJcbiAgcmV0dXJuIHJvbGUgPT09ICdBRE1JTicgfHwgcm9sZSA9PT0gJ09QRVJBVE9SJztcclxufVxyXG5cclxuZXhwb3J0IGZ1bmN0aW9uIGNhblZpZXdBdWRpdExvZ3Mocm9sZTogUm9sZSk6IGJvb2xlYW4ge1xyXG4gIHJldHVybiByb2xlID09PSAnQURNSU4nO1xyXG59XHJcblxyXG5leHBvcnQgZnVuY3Rpb24gY2FuTWFuYWdlVXNlcnMocm9sZTogUm9sZSk6IGJvb2xlYW4ge1xyXG4gIHJldHVybiByb2xlID09PSAnQURNSU4nO1xyXG59XHJcblxyXG4vLyBVdGlsaXR5IHRvIGhhc2ggcGFzc3dvcmRzXHJcbmV4cG9ydCBhc3luYyBmdW5jdGlvbiBoYXNoUGFzc3dvcmQocGFzc3dvcmQ6IHN0cmluZyk6IFByb21pc2U8c3RyaW5nPiB7XHJcbiAgcmV0dXJuIGhhc2gocGFzc3dvcmQsIDEyKTtcclxufVxyXG5cclxuLy8gQXVkaXQgbG9nZ2luZyBoZWxwZXJcclxuZXhwb3J0IGFzeW5jIGZ1bmN0aW9uIGxvZ0F1ZGl0QWN0aW9uKFxyXG4gIHVzZXJJZDogc3RyaW5nLFxyXG4gIGFjdGlvbjogc3RyaW5nLFxyXG4gIHJlc291cmNlOiBzdHJpbmcsXHJcbiAgZGV0YWlscz86IFJlY29yZDxzdHJpbmcsIHVua25vd24+LFxyXG4gIHJlcXVlc3Q/OiB7IGlwPzogc3RyaW5nOyB1c2VyQWdlbnQ/OiBzdHJpbmcgfVxyXG4pIHtcclxuICB0cnkge1xyXG4gICAgYXdhaXQgcHJpc21hLmF1ZGl0TG9nLmNyZWF0ZSh7XHJcbiAgICAgIGRhdGE6IHtcclxuICAgICAgICB1c2VySWQsXHJcbiAgICAgICAgYWN0aW9uLFxyXG4gICAgICAgIHJlc291cmNlLFxyXG4gICAgICAgIGRldGFpbHM6IGRldGFpbHMgfHwge30sXHJcbiAgICAgICAgaXBBZGRyZXNzOiByZXF1ZXN0Py5pcCxcclxuICAgICAgICB1c2VyQWdlbnQ6IHJlcXVlc3Q/LnVzZXJBZ2VudCxcclxuICAgICAgfSxcclxuICAgIH0pO1xyXG4gIH0gY2F0Y2ggKGVycm9yKSB7XHJcbiAgICBjb25zb2xlLmVycm9yKCdGYWlsZWQgdG8gY3JlYXRlIGF1ZGl0IGxvZzonLCBlcnJvcik7XHJcbiAgfVxyXG59XHJcblxyXG5leHBvcnQgZGVmYXVsdCBhdXRoT3B0aW9ucztcclxuIl0sIm5hbWVzIjpbIkNyZWRlbnRpYWxzUHJvdmlkZXIiLCJwcmlzbWEiLCJjb21wYXJlIiwiaGFzaCIsImF1dGhPcHRpb25zIiwicHJvdmlkZXJzIiwibmFtZSIsImNyZWRlbnRpYWxzIiwidXNlcm5hbWUiLCJsYWJlbCIsInR5cGUiLCJwYXNzd29yZCIsImF1dGhvcml6ZSIsIkVycm9yIiwiZW52VXNlcm5hbWUiLCJwcm9jZXNzIiwiZW52IiwiQURNSU5fVVNFUk5BTUUiLCJlbnZQYXNzd29yZCIsIkFETUlOX1BBU1NXT1JEIiwiaWQiLCJyb2xlIiwidXNlciIsImZpbmRVbmlxdWUiLCJ3aGVyZSIsImlzVmFsaWRQYXNzd29yZCIsInBhc3N3b3JkSGFzaCIsInVwZGF0ZSIsImRhdGEiLCJsYXN0TG9naW4iLCJEYXRlIiwiZXJyb3IiLCJjb25zb2xlIiwiY2FsbGJhY2tzIiwiand0IiwidG9rZW4iLCJzZXNzaW9uIiwicGFnZXMiLCJzaWduSW4iLCJzdHJhdGVneSIsIm1heEFnZSIsInNlY3JldCIsIk5FWFRBVVRIX1NFQ1JFVCIsImNhbk1hbmFnZVN0cmF0ZWdpZXMiLCJjYW5NYW5hZ2VQb3NpdGlvbnMiLCJjYW5FZGl0Q29uZmlnIiwiY2FuVXNlRW1lcmdlbmN5Q29udHJvbHMiLCJjYW5WaWV3QXVkaXRMb2dzIiwiY2FuTWFuYWdlVXNlcnMiLCJoYXNoUGFzc3dvcmQiLCJsb2dBdWRpdEFjdGlvbiIsInVzZXJJZCIsImFjdGlvbiIsInJlc291cmNlIiwiZGV0YWlscyIsInJlcXVlc3QiLCJhdWRpdExvZyIsImNyZWF0ZSIsImlwQWRkcmVzcyIsImlwIiwidXNlckFnZW50Il0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(rsc)/./src/lib/auth.ts\n");

/***/ }),

/***/ "(rsc)/./src/lib/prisma.ts":
/*!***************************!*\
  !*** ./src/lib/prisma.ts ***!
  \***************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (__WEBPACK_DEFAULT_EXPORT__),\n/* harmony export */   prisma: () => (/* binding */ prisma)\n/* harmony export */ });\n/* harmony import */ var _prisma_client__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! @prisma/client */ \"@prisma/client\");\n/* harmony import */ var _prisma_client__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(_prisma_client__WEBPACK_IMPORTED_MODULE_0__);\n\nconst globalForPrisma = globalThis;\nconst prisma = globalForPrisma.prisma ?? new _prisma_client__WEBPACK_IMPORTED_MODULE_0__.PrismaClient({\n    log:  true ? [\n        \"query\",\n        \"error\",\n        \"warn\"\n    ] : 0\n});\nif (true) globalForPrisma.prisma = prisma;\n/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (prisma);\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHJzYykvLi9zcmMvbGliL3ByaXNtYS50cyIsIm1hcHBpbmdzIjoiOzs7Ozs7O0FBQThDO0FBRTlDLE1BQU1DLGtCQUFrQkM7QUFJakIsTUFBTUMsU0FDWEYsZ0JBQWdCRSxNQUFNLElBQ3RCLElBQUlILHdEQUFZQSxDQUFDO0lBQ2ZJLEtBQUtDLEtBQXlCLEdBQWdCO1FBQUM7UUFBUztRQUFTO0tBQU8sR0FBRyxDQUFTO0FBQ3RGLEdBQUc7QUFFTCxJQUFJQSxJQUF5QixFQUFjSixnQkFBZ0JFLE1BQU0sR0FBR0E7QUFFcEUsaUVBQWVBLE1BQU1BLEVBQUMiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9wcmVkaWN0Ym90LWFkbWluLy4vc3JjL2xpYi9wcmlzbWEudHM/MDFkNyJdLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgeyBQcmlzbWFDbGllbnQgfSBmcm9tICdAcHJpc21hL2NsaWVudCc7XHJcblxyXG5jb25zdCBnbG9iYWxGb3JQcmlzbWEgPSBnbG9iYWxUaGlzIGFzIHVua25vd24gYXMge1xyXG4gIHByaXNtYTogUHJpc21hQ2xpZW50IHwgdW5kZWZpbmVkO1xyXG59O1xyXG5cclxuZXhwb3J0IGNvbnN0IHByaXNtYSA9XHJcbiAgZ2xvYmFsRm9yUHJpc21hLnByaXNtYSA/P1xyXG4gIG5ldyBQcmlzbWFDbGllbnQoe1xyXG4gICAgbG9nOiBwcm9jZXNzLmVudi5OT0RFX0VOViA9PT0gJ2RldmVsb3BtZW50JyA/IFsncXVlcnknLCAnZXJyb3InLCAnd2FybiddIDogWydlcnJvciddLFxyXG4gIH0pO1xyXG5cclxuaWYgKHByb2Nlc3MuZW52Lk5PREVfRU5WICE9PSAncHJvZHVjdGlvbicpIGdsb2JhbEZvclByaXNtYS5wcmlzbWEgPSBwcmlzbWE7XHJcblxyXG5leHBvcnQgZGVmYXVsdCBwcmlzbWE7XHJcbiJdLCJuYW1lcyI6WyJQcmlzbWFDbGllbnQiLCJnbG9iYWxGb3JQcmlzbWEiLCJnbG9iYWxUaGlzIiwicHJpc21hIiwibG9nIiwicHJvY2VzcyJdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///(rsc)/./src/lib/prisma.ts\n");

/***/ })

};
;

// load runtime
var __webpack_require__ = require("../../../../webpack-runtime.js");
__webpack_require__.C(exports);
var __webpack_exec__ = (moduleId) => (__webpack_require__(__webpack_require__.s = moduleId))
var __webpack_exports__ = __webpack_require__.X(0, ["vendor-chunks/next","vendor-chunks/next-auth","vendor-chunks/@babel","vendor-chunks/jose","vendor-chunks/openid-client","vendor-chunks/oauth","vendor-chunks/object-hash","vendor-chunks/preact","vendor-chunks/preact-render-to-string","vendor-chunks/uuid","vendor-chunks/yallist","vendor-chunks/lru-cache","vendor-chunks/cookie","vendor-chunks/oidc-token-hash","vendor-chunks/@panva","vendor-chunks/bcryptjs"], () => (__webpack_exec__("(rsc)/./node_modules/next/dist/build/webpack/loaders/next-app-loader.js?name=app%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute&page=%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute&appPaths=&pagePath=private-next-app-dir%2Fapi%2Fauth%2F%5B...nextauth%5D%2Froute.ts&appDir=C%3A%5CUsers%5CSeth%20R%5CDesktop%5Cpredictbot-stack%5Cmodules%5Cadmin_portal%5Csrc%5Capp&pageExtensions=tsx&pageExtensions=ts&pageExtensions=jsx&pageExtensions=js&rootDir=C%3A%5CUsers%5CSeth%20R%5CDesktop%5Cpredictbot-stack%5Cmodules%5Cadmin_portal&isDev=true&tsconfigPath=tsconfig.json&basePath=&assetPrefix=&nextConfigOutput=standalone&preferredRegion=&middlewareConfig=e30%3D!")));
module.exports = __webpack_exports__;

})();