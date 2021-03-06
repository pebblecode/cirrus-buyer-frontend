describe("GOVUK.Analytics", function () {
  var analytics;

  beforeEach(function () {
    window.ga = function() {};
    spyOn(window, 'ga');
  });

  describe('when created', function() {
    var universalSetupArguments;

    beforeEach(function() {
      analytics = new window.GOVUK.Analytics({
        universalId: 'universal-id',
        cookieDomain: 'www.digitalmarketplace.service.gov.uk'
      });
      universalSetupArguments = window.ga.calls.allArgs();
    });

    it('configures a universal tracker', function() {
      expect(universalSetupArguments[0]).toEqual(['create', 'universal-id', {
        'cookieDomain': 'www.digitalmarketplace.service.gov.uk'
      }]);
    });
  })

  describe('when setting up cross-domain tracking', function () {
    var sortCalls = function (calls) {
      var gaMethodCalls = {},
          callNum = calls.length;

      while (callNum--) {
        var method = calls[callNum].args.shift(),
            args = calls[callNum].args;

        if (gaMethodCalls.hasOwnProperty(method)) {
          gaMethodCalls[method].push(args);
        } else {
          gaMethodCalls[method] = [args];
        }
      }
      this._calls = gaMethodCalls;
    };
    sortCalls.prototype.callsTo = function (method) {
      if (this._calls.hasOwnProperty(method)) {
        return this._calls[method];
      }
      return [];
    }; 

    beforeEach(function() {
      window.ga.calls.reset();
      analytics = new window.GOVUK.Analytics({
        universalId: 'universal-id',
        cookieDomain: 'www.digitalmarketplace.service.gov.uk',
        receiveCrossDomainTracking: true
      });
      analytics.trackPageview();
      analytics.addLinkedTrackerDomain('digitalservicesstore.service.gov.uk');
    });

    it('only sets up one tracker', function () {
      var gaMethodCalls = new sortCalls(window.ga.calls.all());
      expect(window.ga.calls.count()).toEqual(5);
      // create tracker
      expect(gaMethodCalls.callsTo('create').length).toEqual(1);
      expect(gaMethodCalls.callsTo('create')[0]).toEqual(['universal-id', { 'cookieDomain': 'www.digitalmarketplace.service.gov.uk', 'allowLinker': true }]);
      // anonymize IP
      expect(gaMethodCalls.callsTo('set').length).toEqual(1);
      expect(gaMethodCalls.callsTo('set')[0]).toEqual(['anonymizeIp', true]);
      // send pageview
      expect(gaMethodCalls.callsTo('send').length).toEqual(1);
      expect(gaMethodCalls.callsTo('send')[0]).toEqual(['pageview']);
      // require linker plugin
      expect(gaMethodCalls.callsTo('require').length).toEqual(1);
      expect(gaMethodCalls.callsTo('require')[0]).toEqual(['linker']);
      // autolink the second domain
      expect(gaMethodCalls.callsTo('linker:autoLink').length).toEqual(1);
      expect(gaMethodCalls.callsTo('linker:autoLink')[0]).toEqual([['digitalservicesstore.service.gov.uk']]);
    });
  });
});
