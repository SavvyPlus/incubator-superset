/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */
(function (global, factory) {
  if (typeof define === 'function' && define.amd) {
    define(['exports', 'react', 'prop-types', '../lib/arePathsEqual', '../lib/String'], factory);
  } else if (typeof exports !== 'undefined') {
    factory(exports, require('react'), require('prop-types'), require('../lib/arePathsEqual'), require('../lib/String'));
  } else {
    const mod = {
      exports: {},
    };
    factory(mod.exports, global.react, global.propTypes, global.arePathsEqual, global.String);
    global.Polyline = mod.exports;
  }
}(this, function (exports, _react, _propTypes, _arePathsEqual, _String) {


  Object.defineProperty(exports, '__esModule', {
    value: true,
  });
  exports.Polyline = undefined;

  const _react2 = _interopRequireDefault(_react);

  const _propTypes2 = _interopRequireDefault(_propTypes);

  function _interopRequireDefault(obj) {
    return obj && obj.__esModule ? obj : {
      default: obj,
    };
  }

  const _extends = Object.assign || function (target) {
    for (let i = 1; i < arguments.length; i++) {
      const source = arguments[i];

      for (const key in source) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
          target[key] = source[key];
        }
      }
    }

    return target;
  };

  function _objectWithoutProperties(obj, keys) {
    const target = {};

    for (const i in obj) {
      if (keys.indexOf(i) >= 0) continue;
      if (!Object.prototype.hasOwnProperty.call(obj, i)) continue;
      target[i] = obj[i];
    }

    return target;
  }

  function _classCallCheck(instance, Constructor) {
    if (!(instance instanceof Constructor)) {
      throw new TypeError('Cannot call a class as a function');
    }
  }

  const _createClass = (function () {
    function defineProperties(target, props) {
      for (let i = 0; i < props.length; i++) {
        let descriptor = props[i];
        descriptor.enumerable = descriptor.enumerable || false;
        descriptor.configurable = true;
        if ('value' in descriptor) descriptor.writable = true;
        Object.defineProperty(target, descriptor.key, descriptor);
      }
    }

    return function (Constructor, protoProps, staticProps) {
      if (protoProps) defineProperties(Constructor.prototype, protoProps);
      if (staticProps) defineProperties(Constructor, staticProps);
      return Constructor;
    };
  }());

  function _possibleConstructorReturn(self, call) {
    if (!self) {
      throw new ReferenceError("this hasn't been initialised - super() hasn't been called");
    }

    return call && (typeof call === 'object' || typeof call === 'function') ? call : self;
  }

  function _inherits(subClass, superClass) {
    if (typeof superClass !== 'function' && superClass !== null) {
      throw new TypeError('Super expression must either be null or a function, not ' + typeof superClass);
    }

    subClass.prototype = Object.create(superClass && superClass.prototype, {
      constructor: {
        value: subClass,
        enumerable: false,
        writable: true,
        configurable: true,
      },
    });
    if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass;
  }

  const evtNames = ['click', 'mouseout', 'mouseover'];

  const wrappedPromise = function wrappedPromise() {
    let wrappedPromise = {},
        promise = new Promise(function (resolve, reject) {
      wrappedPromise.resolve = resolve;
      wrappedPromise.reject = reject;
    });
    wrappedPromise.then = promise.then.bind(promise);
    wrappedPromise.catch = promise.catch.bind(promise);
    wrappedPromise.promise = promise;

    return wrappedPromise;
  };

  const Polyline = exports.Polyline = (function (_React$Component) {
    _inherits(Polyline, _React$Component);

    function Polyline() {
      _classCallCheck(this, Polyline);

      return _possibleConstructorReturn(this, (Polyline.__proto__ ||
        Object.getPrototypeOf(Polyline)).apply(this, arguments));
    }

    _createClass(Polyline, [{
      key: 'componentDidMount',
      value: function componentDidMount() {
        this.polylinePromise = wrappedPromise();
        this.renderPolyline();
      },
    }, {
      key: 'componentDidUpdate',
      value: function componentDidUpdate(prevProps) {
        if (this.props.map !== prevProps.map ||
            !(0, _arePathsEqual.arePathsEqual)(this.props.path, prevProps.path)) {
          if (this.polyline) {
            this.polyline.setMap(null);
          }
          this.renderPolyline();
        }
      },
    }, {
      key: 'componentWillUnmount',
      value: function componentWillUnmount() {
        if (this.polyline) {
          this.polyline.setMap(null);
        }
      },
    }, {
      key: 'renderPolyline',
      value: function renderPolyline() {
        let _this2 = this;

        let _props = this.props,
            map = _props.map,
            google = _props.google,
            path = _props.path,
            strokeColor = _props.strokeColor,
            strokeOpacity = _props.strokeOpacity,
            strokeWeight = _props.strokeWeight,
            props = _objectWithoutProperties(_props, ['map', 'google', 'path', 'strokeColor', 'strokeOpacity', 'strokeWeight']);

        if (!google) {
          return null;
        }

        let params = _extends({
          map,
          path,
          strokeColor,
          strokeOpacity,
          strokeWeight,
        }, props);

        this.polyline = new google.maps.Polyline(params);

        evtNames.forEach(function (e) {
          _this2.polyline.addListener(e, _this2.handleEvent(e));
        });

        this.polylinePromise.resolve(this.polyline);
      },
    }, {
      key: 'getPolyline',
      value: function getPolyline() {
        return this.polylinePromise;
      },
    }, {
      key: 'handleEvent',
      value: function handleEvent(evt) {
        let _this3 = this;

        return function (e) {
          let evtName = 'on' + (0, _String.camelize)(evt);
          if (_this3.props[evtName]) {
            _this3.props[evtName](_this3.props, _this3.polyline, e);
          }
        };
      },
    }, {
      key: 'render',
      value: function render() {
        return null;
      },
    }]);

    return Polyline;
  }(_react2.default.Component));

  Polyline.propTypes = {
    path: _propTypes2.default.array,
    strokeColor: _propTypes2.default.string,
    strokeOpacity: _propTypes2.default.number,
    strokeWeight: _propTypes2.default.number,
  };

  evtNames.forEach(function (e) {
    return Polyline.propTypes[e] = _propTypes2.default.func;
  });

  Polyline.defaultProps = {
    name: 'Polyline',
  };

  exports.default = Polyline;
}));
